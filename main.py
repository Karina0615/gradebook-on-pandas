'''Calculating students grades by combining dada from different sourses.
-roster
-homework&exam grades
-quiz grades

'''

from pathlib import Path
import pandas as pd
import numpy as np

HERE = Path(__file__).parent
DATA_FOLDER = HERE / "Import"
DATA_FOLDER2 = HERE / "Export"

'''LOADING THE DATA'''
roster = pd.read_csv(
    DATA_FOLDER / 'roster.csv',
    converters={"NetID":str.lower, "Email Address": str.lower},
    usecols=["Section", "Email Address", "NetID"],
    index_col = "NetID"
)

hw_exam_grades = pd.read_csv(
    DATA_FOLDER / 'hw_exam_grades.csv',
    converters = {"SID": str.lower},
    usecols = lambda x: "Submission" not in x,
    index_col = "SID"
)

quiz_grades = pd.DataFrame()
for file_path in DATA_FOLDER.glob("quiz_*_grades.csv"):
    quiz_name = " ".join(file_path.stem.title().split("_")[:2])
    quiz = pd.read_csv(
        file_path,
        converters={"Email": str.lower},
        usecols=["Email", "Grade"],
        index_col="Email"
    ).rename(columns={"Grade": quiz_name})
    quiz_grades = pd.concat([quiz_grades, quiz], axis=1)


'''MERGING DATA'''
final_data = pd.merge(roster, hw_exam_grades, left_index=True, right_index=True)

final_data = pd.merge(final_data, quiz_grades, left_on="Email Address", right_index=True)

final_data = final_data.fillna(0)

'''Calculating grades'''
#Calculating the Exam total score
n_exam = 3
for n in range(1, n_exam+1):
    final_data[f"Exam {n} Score"] = (
      final_data[f"Exam {n}"] / final_data[f"Exam {n} - Max Points"]  
    )


'''Calculating the hw scores in 2 ways
1.By total score: Sum the raw scores and maximum points independently, then take the ratio.
2.By average score: Divide each raw score by its respective maximum points, 
then take the sum of these ratios and divide the total by the number of assignments.
'''
homework_scores = final_data.filter(regex=r"^Homework \d\d?$", axis=1)
homework_max_points = final_data.filter(regex=r"^Homework \d\d? -", axis=1)
hw_max_renamed = homework_max_points.set_axis(homework_scores.columns, axis=1)

sum_of_hw_scores = homework_scores.sum(axis=1)
sum_of_hw_max = homework_max_points.sum(axis=1)
average_hw_scores = (homework_scores / hw_max_renamed).sum(axis=1)

final_data["Total Homework"] = sum_of_hw_scores / sum_of_hw_max
final_data["Average Homework"] = average_hw_scores / homework_scores.shape[1]
final_data["Homework Score"] = final_data[["Total Homework", "Average Homework"]].max(axis=1)


'''Calculating the Quiz Score in 2 ways
1.By total score: Sum the raw scores and maximum points independently, then take the ratio.
2.By average score: Divide each raw score by its respective maximum points, 
then take the sum of these ratios and divide the total by the number of assignments.
'''
quiz_score = final_data.filter(regex=r"^Quiz \d$", axis=1)
#we don`t have this in our data sourse, that is why I should create it`
quix_max_points = pd.Series(
    {"Quiz 1": 11, "Quiz 2": 15, "Quiz 3": 17, "Quiz 4": 14, "Quiz 5": 12}
)
average_quiz_scores = (quiz_score / quix_max_points).sum(axis=1)

sum_of_quiz_scores = quiz_score.sum(axis=1)
sum_of_quiz_max = quix_max_points.sum()

final_data["Total Quizzes"] = sum_of_quiz_scores / sum_of_quiz_max
final_data["Average Quizzes"] = average_quiz_scores / quiz_score.shape[1]
final_data["Quiz Score"] = final_data[["Total Quizzes", "Average Quizzes"]].max(axis=1)


'''Calculating the Final(Letter) Score
'''
score_influence = pd.Series(
    {
        "Exam 1 Score": 0.05,
        "Exam 2 Score": 0.1,
        "Exam 3 Score": 0.15,
        "Quiz Score": 0.30,
        "Homework Score": 0.4
    }
)
final_data["Final Score"] = (final_data[score_influence.index]* score_influence).sum(axis=1)
final_data["Ceiling Score"] = np.ceil(final_data["Final Score"]*100)


#Mapping the Letter Score
grades = {
    90: "A",
    80: "B",
    70: "C",
    60: "D",
    0: "F"
}

def grade_mapping(value):
    for key, letter in grades.items():
        if value >= key:
            return letter

letter_grades = final_data["Ceiling Score"].map(grade_mapping)
final_data["Final Grade"] = pd.Categorical(letter_grades, categories=grades.values(), ordered=True)       


'''
Grouping the Data
'''
for section, table in final_data.groupby("Section"):
    section_file = DATA_FOLDER2 / f'Section {section} Grades.csv'
    num_students = table.shape[0]
    print(
        f"In Section {section} there are {num_students} students saved to"
        f"file {section_file}."
    )
    table.sort_values(by= ["Last Name", "First Name"]).to_csv(section_file)

final_file = DATA_FOLDER2 / f"Final_file.csv"
final_save = final_data.to_csv(final_file) 

print(final_data)