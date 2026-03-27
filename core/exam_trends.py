from typing import List

EXAM_TRENDS = {
    "JEE Main": {
        "Physics": {"topics": [
            {"name": "Mechanics", "weightage": 25, "difficulty": "medium", "frequency": "every_year", "avg_questions": 7},
            {"name": "Electrostatics", "weightage": 15, "difficulty": "medium", "frequency": "every_year", "avg_questions": 4},
            {"name": "Thermodynamics", "weightage": 10, "difficulty": "hard", "frequency": "every_year", "avg_questions": 3},
            {"name": "Optics", "weightage": 10, "difficulty": "medium", "frequency": "every_year", "avg_questions": 3},
            {"name": "Modern Physics", "weightage": 12, "difficulty": "easy", "frequency": "every_year", "avg_questions": 4},
            {"name": "Waves", "weightage": 8, "difficulty": "medium", "frequency": "alternate_years", "avg_questions": 2},
            {"name": "Magnetism", "weightage": 10, "difficulty": "medium", "frequency": "every_year", "avg_questions": 3},
            {"name": "Current Electricity", "weightage": 10, "difficulty": "easy", "frequency": "every_year", "avg_questions": 3},
        ], "total_questions": 30, "total_marks": 100},
        "Chemistry": {"topics": [
            {"name": "Organic Chemistry", "weightage": 35, "difficulty": "hard", "frequency": "every_year", "avg_questions": 10},
            {"name": "Physical Chemistry", "weightage": 30, "difficulty": "medium", "frequency": "every_year", "avg_questions": 9},
            {"name": "Inorganic Chemistry", "weightage": 35, "difficulty": "easy", "frequency": "every_year", "avg_questions": 10},
        ], "total_questions": 30, "total_marks": 100},
        "Mathematics": {"topics": [
            {"name": "Calculus", "weightage": 25, "difficulty": "hard", "frequency": "every_year", "avg_questions": 7},
            {"name": "Algebra", "weightage": 25, "difficulty": "medium", "frequency": "every_year", "avg_questions": 7},
            {"name": "Coordinate Geometry", "weightage": 15, "difficulty": "medium", "frequency": "every_year", "avg_questions": 5},
            {"name": "Trigonometry", "weightage": 10, "difficulty": "easy", "frequency": "every_year", "avg_questions": 3},
            {"name": "Vectors & 3D", "weightage": 10, "difficulty": "medium", "frequency": "every_year", "avg_questions": 3},
            {"name": "Probability & Statistics", "weightage": 10, "difficulty": "medium", "frequency": "every_year", "avg_questions": 3},
        ], "total_questions": 30, "total_marks": 100},
    },
    "JEE Advanced": {
        "Physics": {"topics": [
            {"name": "Mechanics", "weightage": 30, "difficulty": "hard", "frequency": "every_year", "avg_questions": 6},
            {"name": "Electrostatics", "weightage": 15, "difficulty": "hard", "frequency": "every_year", "avg_questions": 3},
            {"name": "Thermodynamics", "weightage": 12, "difficulty": "hard", "frequency": "every_year", "avg_questions": 2},
            {"name": "Optics", "weightage": 10, "difficulty": "hard", "frequency": "every_year", "avg_questions": 2},
            {"name": "Modern Physics", "weightage": 10, "difficulty": "medium", "frequency": "every_year", "avg_questions": 2},
            {"name": "Rotational Motion", "weightage": 13, "difficulty": "hard", "frequency": "every_year", "avg_questions": 3},
            {"name": "Waves", "weightage": 10, "difficulty": "hard", "frequency": "alternate_years", "avg_questions": 2},
        ], "total_questions": 20, "total_marks": 60},
        "Chemistry": {"topics": [
            {"name": "Organic Chemistry", "weightage": 35, "difficulty": "hard", "frequency": "every_year", "avg_questions": 7},
            {"name": "Physical Chemistry", "weightage": 35, "difficulty": "hard", "frequency": "every_year", "avg_questions": 7},
            {"name": "Inorganic Chemistry", "weightage": 30, "difficulty": "medium", "frequency": "every_year", "avg_questions": 6},
        ], "total_questions": 20, "total_marks": 60},
        "Mathematics": {"topics": [
            {"name": "Calculus", "weightage": 30, "difficulty": "hard", "frequency": "every_year", "avg_questions": 6},
            {"name": "Algebra", "weightage": 25, "difficulty": "hard", "frequency": "every_year", "avg_questions": 5},
            {"name": "Coordinate Geometry", "weightage": 15, "difficulty": "hard", "frequency": "every_year", "avg_questions": 3},
            {"name": "Vectors & 3D", "weightage": 10, "difficulty": "hard", "frequency": "every_year", "avg_questions": 2},
            {"name": "Probability", "weightage": 10, "difficulty": "hard", "frequency": "every_year", "avg_questions": 2},
            {"name": "Trigonometry", "weightage": 10, "difficulty": "medium", "frequency": "alternate_years", "avg_questions": 2},
        ], "total_questions": 20, "total_marks": 60},
    },
    "NEET": {
        "Physics": {"topics": [
            {"name": "Mechanics", "weightage": 25, "difficulty": "medium", "frequency": "every_year", "avg_questions": 12},
            {"name": "Electrostatics", "weightage": 12, "difficulty": "medium", "frequency": "every_year", "avg_questions": 6},
            {"name": "Modern Physics", "weightage": 15, "difficulty": "easy", "frequency": "every_year", "avg_questions": 7},
            {"name": "Optics", "weightage": 12, "difficulty": "medium", "frequency": "every_year", "avg_questions": 6},
            {"name": "Thermodynamics", "weightage": 10, "difficulty": "medium", "frequency": "every_year", "avg_questions": 5},
            {"name": "Current Electricity", "weightage": 12, "difficulty": "easy", "frequency": "every_year", "avg_questions": 6},
            {"name": "Magnetism", "weightage": 8, "difficulty": "medium", "frequency": "every_year", "avg_questions": 4},
            {"name": "Waves", "weightage": 6, "difficulty": "easy", "frequency": "alternate_years", "avg_questions": 3},
        ], "total_questions": 45, "total_marks": 180},
        "Chemistry": {"topics": [
            {"name": "Organic Chemistry", "weightage": 30, "difficulty": "medium", "frequency": "every_year", "avg_questions": 14},
            {"name": "Physical Chemistry", "weightage": 30, "difficulty": "medium", "frequency": "every_year", "avg_questions": 14},
            {"name": "Inorganic Chemistry", "weightage": 40, "difficulty": "easy", "frequency": "every_year", "avg_questions": 18},
        ], "total_questions": 45, "total_marks": 180},
        "Biology": {"topics": [
            {"name": "Botany", "weightage": 25, "difficulty": "medium", "frequency": "every_year", "avg_questions": 22},
            {"name": "Human Physiology", "weightage": 20, "difficulty": "medium", "frequency": "every_year", "avg_questions": 18},
            {"name": "Genetics", "weightage": 15, "difficulty": "hard", "frequency": "every_year", "avg_questions": 14},
            {"name": "Ecology", "weightage": 12, "difficulty": "easy", "frequency": "every_year", "avg_questions": 11},
            {"name": "Cell Biology", "weightage": 10, "difficulty": "medium", "frequency": "every_year", "avg_questions": 9},
            {"name": "Zoology", "weightage": 10, "difficulty": "medium", "frequency": "every_year", "avg_questions": 9},
            {"name": "Evolution", "weightage": 8, "difficulty": "easy", "frequency": "alternate_years", "avg_questions": 7},
        ], "total_questions": 90, "total_marks": 360},
    },
}


def get_exam_trends(exam_type: str) -> dict:
    return EXAM_TRENDS.get(exam_type, {})


def get_priority_topics(exam_type: str, student_subjects: dict) -> List[dict]:
    trends = get_exam_trends(exam_type)
    if not trends:
        return []
    priority_topics = []
    for subject, subject_data in trends.items():
        if subject not in student_subjects:
            continue
        student_score = student_subjects[subject]
        for topic in subject_data.get("topics", []):
            urgency = topic["weightage"] * (100 - student_score) / 100
            priority_topics.append({
                "subject": subject, "topic": topic["name"], "weightage": topic["weightage"],
                "difficulty": topic["difficulty"], "student_score": student_score,
                "urgency_score": round(urgency, 1),
            })
    priority_topics.sort(key=lambda x: x["urgency_score"], reverse=True)
    return priority_topics
