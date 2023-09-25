import os
import openai
import json
import pycld2 as cld2
import random
from datetime import datetime


from dotenv import load_dotenv
from db.supabase import get_sb
from services.text_extract import get_token_count
from db.database import get_content, get_assessment_responses, get_activity_assessment,get_question,get_taxonomy,get_student_id,get_all_question, jaccard_similarity

load_dotenv()

class QuestionGenerator:
    def __init__(self, user_id, course_id, chapter_id):
        self.user_id = user_id
        self.course_id = course_id
        self.chapter_id = chapter_id
        self.generator = QuestionGeneratorFunctionCall()
        self.generated_questions = set()

    def save(self):
        result = get_sb().table("assessmentActivities").insert({"user_id":self.user_id,"course_id":self.course_id,"chapter_id":self.chapter_id,
                                                       "score":"0"}).execute()
        results = result.data
        assessment_id = results[0]["id"]
        start_time = results[0]["start_time"]
        return assessment_id, start_time

    def init_QuestionGenerator(self):
        contents, num_topic_ids, topic_ids = get_content(self.chapter_id)
        question_distributors = QuestionDistributor()
        all_json_data = []
        for topic_id, content in zip(topic_ids, contents):
            question_distributors.add_topic(topic_id)
        questions_per_chapter_split = question_distributors.generate_questions_per_chapter()
        for topic_id, content in zip(topic_ids, contents):
            print("-----")
            print(topic_id)
            if topic_id in questions_per_chapter_split:
                topic_json_data = []
                _, _, _, detected_language = cld2.detect(content,  returnVectors=True)
                detected_language = detected_language[0][2]
                for difficulty in ["easy", "medium"]:
                    num_question = questions_per_chapter_split.get(topic_id, {}).get(difficulty) 
                    print(difficulty)
                    print(num_question)
                    json_data_items = self.generate_questions_for_topic(detected_language, content, num_question, topic_id, difficulty)
                    topic_json_data.extend(json_data_items) 
                all_json_data.extend(topic_json_data)
                format_json_data = json.dumps(all_json_data, indent=4)
        return format_json_data
            
    def generate_questions_for_topic(self, detected_language, content, num_question, topic_id, difficulty):
        token_count, tokens = get_token_count(content, "cl100k_base")
        difficulty_criteria = {
            "easy": {
                "prompt_suffix": "Test basic facts and concepts, simple definitions or label identification, and beginner level, surface understanding",
            },
            "medium": {
                "prompt_suffix": "Apply key principles and relationships, may involve sequences, processes or classifications, and require deeper understanding",
            },
        }
        self.existing_questions = get_all_question()

        difficulty_info = difficulty_criteria.get(difficulty)
        prompt_suffix = difficulty_info["prompt_suffix"]
        similarity_threshold = 0.9

        user_prompt = f"""Generate 15 unique True/False questions suitable for Form 4 students in Malaysia based on the provided text content.
        As an expert in creating such questions, I'd like you to follow these specific instructions for {difficulty} questions:
        - Focus on this criteria {prompt_suffix}.
        - Change the language to {detected_language} language and consistent across all questions.
        - Randomly shuffle the answers (True/False) for each question.

        Here is the text content:
        "{content}"
        """

        model = "gpt-3.5-turbo" if token_count < 2000 else "gpt-3.5-turbo-16k"
        response = self.generator.generate_questions(user_prompt, model)
        question_dict = json.loads(response.function_call.arguments)
        questions = question_dict["question"]
        options = ['Betul', 'Salah']
        answers = question_dict["answer"]
        filtered_questions = []
        filtered_answers = []
        
        for question, answer in zip(questions, answers):
            is_similar = any(
                jaccard_similarity(existing_question, question) > similarity_threshold 
                for existing_question in self.existing_questions
            )
            
            if not is_similar:
               filtered_questions.append(question)
               filtered_answers.append(answer)

        # Randomly select num_question questions from filtered_questions
        if len(filtered_questions) <= num_question:
            selected_questions = filtered_questions
            selected_answers = filtered_answers
        else:
            selected_indices = random.sample(range(len(filtered_questions)), num_question)
            selected_questions = [filtered_questions[i] for i in selected_indices]
            selected_answers = [filtered_answers[i] for i in selected_indices]
        questions_data = []
        i = 0
        for question, answer in zip(selected_questions, selected_answers):
            print(i)
            i += 1
            print(question)
            result = get_sb().table("questions").insert({
                "topic_id": f"{topic_id}","question_text": f"{question}",
                "options": f"{options}","answer": f"{answer}","difficulty": f"{difficulty}"}).execute()
            results = result.data
            question_id = results[0]["id"]
            # question_id = get_question_id(question)
            
            question_data = {
                "no" : i,
                "topic_id": topic_id,
                "question_id": question_id,
                "question_text": question,
                "options": options,
                "answer": answer,
                "difficulty": difficulty
            }
            questions_data.append(question_data)
        return questions_data

class QuestionGeneratorFunctionCall:
    def __init__(self):
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        openai.api_key = self.openai_key

    def generate_questions(self, user_prompt, model):
        """Generate true or false questions by using OpenAI Calling Function."""
        function_descriptions = [
            {
                "name": "truefalsequestion",
                "description": "Generate question based on the provided text content that mentioned in prompt",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A single or list of True/false question",
                        },
                        "answer": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "A single or list of correct answer for the question",
                        }, 
                    },
                    "required": ["question", "answer"],
                },
            }
        ]
        conversation = [{"role": "user", "content": user_prompt}]
        response = openai.ChatCompletion.create(
            model=model,
            messages=conversation,
            functions=function_descriptions,
            function_call="auto",
            temperature=0.7
            )
        return response.choices[0].message

class QuestionDistributor:
    def __init__(self):
        self.topic_ids = []
        self.total_questions = 30

    def add_topic(self, topic_id):
        self.topic_ids.append(topic_id)

    def generate_questions_per_chapter(self):
        num_topics = len(self.topic_ids)
        questions_per_chapter = {}
        questions_per_topic = self.total_questions // num_topics  # Integer division to distribute equally
        
        # Initialize questions_per_chapter with equal distribution
        for topic_id in self.topic_ids:
            questions_per_chapter[topic_id] = questions_per_topic
        
        # Distribute any remaining questions randomly
        remaining_questions = self.total_questions % num_topics
        if remaining_questions > 0:
            for _ in range(remaining_questions):
                random_topic = random.choice(self.topic_ids)
                questions_per_chapter[random_topic] += 1

        # Split questions for each topic_id into "easy" and "medium" categories
        questions_per_chapter_split = {}
        for topic_id, num_questions in questions_per_chapter.items():
            easy_questions = int(num_questions * 0.4)  # 40% for easy
            medium_questions = num_questions - easy_questions  # Remaining for medium
            questions_per_chapter_split[topic_id] = {"easy": easy_questions, "medium": medium_questions}
        
        return questions_per_chapter_split

class ProfilingEngine:
    
    def __init__(self):
        self.profile_data = {}
        self.topic_data = {}
        self.topic_question_summary = {}

    def get_response(self, question_id):
        response_id, assessment_activity_id, answer_sequence, duration = get_assessment_responses(question_id)
        user_id, course_id, chapter_id, start_time, end_time = get_activity_assessment(assessment_activity_id)
        question_text, topic_id, answer, difficulty, options = get_question(question_id)

        gaps = []
        gaps.append('Slow on questions' if duration > 30 else 'Normal on questions')
        gaps.append('Struggles with answer' if len(answer_sequence) > 1 else 'Normal with answer')
        gaps.append('Answer is correct' if answer_sequence[-1]["answer"] == answer else 'Answer is incorrect')

        if topic_id not in self.topic_question_summary:
            self.topic_question_summary[topic_id] = {}

        self.topic_question_summary[topic_id][question_id] = {
            "slow_answer_question": 0,
            "normal_answer_question": 0,
            "answer_changed": 0,
            "answer_not_changed": 0,
            "answer_is_correct": 0,
            "answer_is_incorrect": 0,
            "difficulty": difficulty
        }

        self.topic_question_summary[topic_id][question_id]["slow_answer_question"] += 1 if 'Slow on questions' in gaps else 0
        self.topic_question_summary[topic_id][question_id]["normal_answer_question"] += 1 if 'Normal on questions' in gaps else 0
        self.topic_question_summary[topic_id][question_id]["answer_changed"] += 1 if 'Struggles with answer' in gaps else 0
        self.topic_question_summary[topic_id][question_id]["answer_not_changed"] += 1 if 'Normal with answer' in gaps else 0
        self.topic_question_summary[topic_id][question_id]["answer_is_correct"] += 1 if 'Answer is correct' in gaps else 0
        self.topic_question_summary[topic_id][question_id]["answer_is_incorrect"] += 1 if 'Answer is incorrect' in gaps else 0


        taxonomy = get_taxonomy(course_id,chapter_id,topic_id)
        response_data = {
            "response_id": response_id,
            "user_id": user_id,
            "assessment_activity_id": assessment_activity_id,
            "duration": duration,
            "start_time": start_time,
            "end_time": end_time,
            "question": {
                "question_id": question_id,
                "taxonomy": taxonomy,
                "question_text": question_text,
                "answer_sequence": [
                    {
                        "answer": item["answer"],
                        "duration": item["duration"]
                    }
                    for item in answer_sequence
                ],
                "answer": answer,
                "difficulty": difficulty,
                "gaps": gaps
            }
        }

        if topic_id not in self.topic_data:
            self.topic_data[topic_id] = {
                "total_responses": 0,
                "correct_responses": 0,
                "total_duration": 0
            }

        topic_data = self.topic_data[topic_id]
        topic_data["total_responses"] += 1

        if response_data["question"]["answer_sequence"][-1]["answer"] == response_data["question"]["answer"]:
            topic_data["correct_responses"] += 1

        topic_data["total_duration"] += response_data["duration"]

        if user_id not in self.profile_data:
            self.profile_data[user_id] = []
        self.profile_data[user_id].append(response_data)
        return course_id, chapter_id, user_id

    def analyze_responses(self,question_ids):
        for question_id in question_ids:
            course_id, chapter_id, user_id = self.get_response(question_id)

        formatted_profile_data = self.format_profile_data()
        formatted_topic_proficiency = self.calculate_topic_proficiency(course_id, chapter_id)

        merged_data = {
            "profile": formatted_profile_data,
            "proficiency": formatted_topic_proficiency
        }
        merged_json = json.dumps(merged_data, indent=4)
        profile_by_question = json.dumps(formatted_profile_data, indent=4)
        proficiency = json.dumps(formatted_topic_proficiency, indent=4)
        print("Formatted Profile Data:")
        print(profile_by_question)
        print("Topic Proficiency:")
        print(proficiency)
        return proficiency, user_id
    
    def format_profile_data(self):
        formatted_profile_data = {}
        for user_id, responses in self.profile_data.items():
            formatted_responses = []
            for response in responses:
                formatted_response = {
                    "response_id": response["response_id"],
                    "duration": response["duration"],
                    "start_time": response["start_time"],
                    "end_time": response["end_time"],
                    "question": response["question"]
                }
                formatted_responses.append(formatted_response)
            formatted_profile_data[user_id] = formatted_responses
        return formatted_profile_data

    def calculate_topic_proficiency(self, course_id, chapter_id):
        formatted_topic_proficiency = {}
        for topic_id, data in self.topic_data.items():
            taxonomy = get_taxonomy(course_id, chapter_id, topic_id)
            total_responses = data["total_responses"]
            proficiency = (data["correct_responses"] / total_responses) if total_responses > 0 else 0
            difficulty_statistics = self.calculate_difficulty_statistics(topic_id)
            # Get all response_id values
            response_ids = []
            for user_responses in self.profile_data.values():
                for response in user_responses:
                    if response["question"]["taxonomy"] == taxonomy:
                        response_ids.append(response["response_id"])
            formatted_topic_proficiency[topic_id] = {
                "taxonomy": taxonomy,
                "response_ids": response_ids, 
                "total_responses": total_responses,
                "correct_responses": data["correct_responses"],
                "total_duration": f"{data['total_duration']} seconds",
                "average_duration": f"{data['total_duration'] / total_responses:.2f} seconds",
                "proficiency": f"{proficiency:.2f}",
                "proficiency_percentage": f"{proficiency * 100:.2f}%",
                "question_summary": difficulty_statistics
            }
        return formatted_topic_proficiency

    def calculate_difficulty_statistics(self,topic_id):
        difficulty_statistics = {
            "easy": {
                "slow_answer_question": 0,
                "normal_answer_question": 0,
                "answer_changed": 0,
                "answer_not_changed": 0,
                "answer_is_correct": 0,
                "answer_is_incorrect": 0
            },
            "medium": {
                "slow_answer_question": 0,
                "normal_answer_question": 0,
                "answer_changed": 0,
                "answer_not_changed": 0,
                "answer_is_correct": 0,
                "answer_is_incorrect": 0
            }
        }

        for question_summary in self.topic_question_summary.get(topic_id, {}).values():
            difficulty = question_summary["difficulty"]
            for key in difficulty_statistics[difficulty]:
                difficulty_statistics[difficulty][key] += question_summary[key]
        return difficulty_statistics

    def save_profile(self,proficiency_json, user_id):
        student_id = get_student_id(user_id)
        date_object = datetime.strptime("12 May 1995", "%d %B %Y")
        formatted_date = date_object.strftime("%Y-%m-%d") 
        result = get_sb().table("profiles").insert({"student_id":student_id,"metadata":proficiency_json,"last_updated":"2023-09-18 09:29:00+00",
                                                       "dob":formatted_date}).execute()
        return proficiency_json