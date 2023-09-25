import json
from nltk.metrics.distance import jaccard_distance
from db.supabase import get_sb

def upload_file(bucket_name, file_path, file_name):
    file_content = ""
    with open(file_path, "r") as file:
        file_content = file.read()
    file_location = f"{bucket_name}/{file_name}"
    get_sb().storage.from_(bucket_name).upload(file_location, file_content)
    return file_location

def delete_file(file_location):
    get_sb().storage.from_(file_location).delete()
    return

def log_job(message):
    get_sb().table("jobs").insert({"status": message}).execute()

def get_file_location(chapter_id):
    result = get_sb().table("chapters").select("file_location").eq("id", chapter_id).execute()
    return result["file_location"]

def get_course_directory_name(course):
    directory_name = f"{course.data[0]['name']}-{course.data[0]['course_code']}"
    directory_name = directory_name.lower().replace(" ", "_")
    return directory_name

def get_chapter_directory_name(chapter):
    return str(chapter.data[0]['chapter_index'])

def get_all_question():
    results = get_sb().table("questions").select("question_text").execute()
    result = results.data
    questions = []
    for item in result:
        question = item['question_text']
        questions.append(question)
    return questions

def get_question_id(question):
    results = get_sb().table("questions").select("id").eq("question_text", question).execute()
    result = results.data
    question_id = result[0]["id"]
    return question_id

def jaccard_similarity(text1, text2):
        distance = jaccard_distance(set(text1), set(text2))
        similarity = 1 - distance
        return similarity

def get_content(chapter_id):
    content_data = get_sb().table('topics').select("metadata","id").eq("chapter_id", chapter_id).execute()
    content_list = content_data.data
    contents = []
    topic_ids = []
    for item in content_list:
        topic_id = item['id']
        metadata = item['metadata']
        proper_json_string = metadata.replace("'", "\"")
        metadata = json.loads(proper_json_string)
        content = metadata['content']
        contents.append(content)
        topic_ids.append(topic_id)
    num_topic_ids = len(topic_ids)
    return contents, num_topic_ids, topic_ids

def get_topicscore(topic_id):
    topic_scores = get_sb().table('topics').select("topic_score").eq("id", topic_id).execute()
    topic_score = topic_scores.data
    topic_score = topic_score[0]["topic_score"]
    return topic_score

def get_assessment_responses(question_id):
    questions = get_sb().table('assessmentResponses').select("id","assessment_activity_id","answer_sequence", "duration").eq("question_id", question_id).execute()
    question = questions.data
    response_id = question[0]["id"]
    assessment_activity_id = question[0]["assessment_activity_id"]
    answer_sequence = question[0]["answer_sequence"]
    duration = question[0]["duration"]
    return response_id, assessment_activity_id, answer_sequence, duration

def get_activity_assessment(activity_id):
    activities = get_sb().table('assessmentActivities').select("user_id","course_id","chapter_id", "start_time", "end_time").eq("id", activity_id).execute()
    activity = activities.data
    user_id = activity[0]["user_id"]
    course_id = activity[0]["course_id"]
    chapter_id = activity[0]["chapter_id"]
    start_time = activity[0]["start_time"]
    end_time = activity[0]["end_time"]
    return user_id, course_id, chapter_id, start_time, end_time

def get_question(question_id):
    questions = get_sb().table('questions').select("question_text","topic_id","answer","difficulty", "options").eq("id", question_id).execute()
    question = questions.data
    question_text = question[0]["question_text"]
    topic_id = question[0]["topic_id"]
    answer = question[0]["answer"]
    difficulty = question[0]["difficulty"]
    options = question[0]["options"]
    return question_text, topic_id, answer, difficulty, options

def get_taxonomy(course_id,chapter_id,topic_id):
    course_names = get_sb().table('courses').select("name").eq("id", course_id).execute()
    courses_name = course_names.data
    course_name = courses_name[0]["name"]

    chapter_names = get_sb().table('chapters').select("name").eq("id", chapter_id[0]).execute()
    print(chapter_names)
    chapters_name = chapter_names.data
    print(chapters_name)
    chapter_name = chapters_name[0]["name"]
    print(chapter_name)

    topic_names = get_sb().table('topics').select("name").eq("id", topic_id).execute()
    topics_name = topic_names.data
    topic_name = topics_name[0]["name"]

    # Remove ".md" extension from topic name
    if topic_name.endswith(".md"):
        topic_name = topic_name[:-3]

    taxonomy = ",".join(map(str, (course_name, chapter_name, topic_name)))
    return taxonomy

def get_student_id(user_id):
    student_ids = get_sb().table('students').select("id").eq("user_id", user_id).execute()
    student_id = student_ids.data
    student_id = student_id[0]["id"]
    return student_id