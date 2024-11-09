import pandas as pd

# Load the CourseDetails dataset
df_course_details = pd.read_csv('CourseDetails.csv')

# Select the first 5 unique course numbers for preferences
unique_courses = df_course_details['CourseNo'].unique()

# Sample data for the LecturerPreferences dataset with 9 fictitious staff names
data = {
    "Sno": range(1, 10),
    "FacultyID": [f"F00{i}" for i in range(1, 10)],
    "FacultyName": ["Dr. Alice Johnson", "Dr. Bob Smith", "Dr. Carol White", 
                    "Dr. David Brown", "Dr. Eve Davis", "Dr. Fiona Green", 
                    "Dr. George Harris", "Dr. Hannah Martin", "Dr. Ian Clark"],
    "MaxLoad": [12] * 9,
    "Pref1": [unique_courses[i % len(unique_courses)] for i in range(9)],
    "Pref2": [unique_courses[(i + 1) % len(unique_courses)] for i in range(9)],
    "Pref3": [unique_courses[(i + 2) % len(unique_courses)] for i in range(9)],
    "Pref4": [unique_courses[(i + 3) % len(unique_courses)] for i in range(9)],
    "Pref5": [unique_courses[(i + 4) % len(unique_courses)] for i in range(9)]
}

# Create a DataFrame
df_sample_lecturer_prefs = pd.DataFrame(data)

# Save the DataFrame to a CSV file
df_sample_lecturer_prefs.to_csv('sample_lecturer_preferences.csv', index=False)
