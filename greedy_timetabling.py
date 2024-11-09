import pandas as pd
import networkx as nx
import datetime
from itertools import combinations
from copy import deepcopy

# Load datasets
df_advised_courses = pd.read_csv('C:\\Users\\ispace\\Desktop\\GreedyTimetabling\\AdvisedCourses.csv')
df_course_details = pd.read_csv('C:\\Users\\ispace\\Desktop\\GreedyTimetabling\\CourseDetails.csv')
df_rooms = pd.read_csv('C:\\Users\\ispace\\Desktop\\GreedyTimetabling\\Rooms.csv')
df_lecturer_prefs = pd.read_csv('C:\\Users\\ispace\\Desktop\\GreedyTimetabling\\LecturerPreferences.csv')

# Step 1: Preprocess and Create Mappings
def load_and_preprocess_data():
    # Map CourseNo to CourseName for quick lookup
    course_name_map = df_course_details.set_index('CourseNo')['CourseName'].to_dict()

    # Map CourseNo to RoomType
    course_room_map = df_course_details.set_index('CourseNo')['RoomType'].to_dict()

    # Map CourseNo to its details
    course_details_map = df_course_details.set_index('CourseNo').to_dict('index')

    # Map RoomNo to its capacity
    room_capacity_map = df_rooms.set_index('RoomNo')['Capacity'].to_dict()

    # Map FacultyID to their preferences and max load
    lecturer_prefs_map = df_lecturer_prefs.set_index('FacultyID').to_dict('index')

    return df_advised_courses, course_name_map, course_room_map, course_details_map, room_capacity_map, lecturer_prefs_map


# Function to calculate the clash count between two courses
def get_clash_count(course1, course2, df):
    students_course1 = set(df[df['CourseNo'] == course1]['StudentNo'])
    students_course2 = set(df[df['CourseNo'] == course2]['StudentNo'])
    return len(students_course1 & students_course2)

# Step 2: Graph Construction and Maximal Cliques Identification
def construct_graph_and_find_cliques(df):
    # List of all unique courses
    courses = df['CourseNo'].unique()

    # Calculating clashes
    clashes = []
    for course1, course2 in combinations(courses, 2):
        clash_count = get_clash_count(course1, course2, df)
        if clash_count > 0:
            clashes.append({'Course1': course1, 'Course2': course2, 'ClashCount': clash_count})

    # Convert to DataFrame
    clashes_df = pd.DataFrame(clashes)

    # Construct graph
    G = nx.Graph()
    for index, row in clashes_df.iterrows():
        G.add_edge(row['Course1'], row['Course2'], weight=row['ClashCount'])

    # Find maximal cliques
    cliques = list(nx.find_cliques(G))
    return cliques

# Step 3: Sort Cliques and Courses
def sort_cliques_by_total_enrollment(cliques, df_course_details):
    # Map CourseNo to NumberOfAdvisedStudents
    advised_students_map = df_course_details.set_index('CourseNo')['NumberOfAdvisedStudents'].to_dict()

    # Function to calculate the total number of advised students in a clique
    def total_students_in_clique(clique):
        return sum(advised_students_map.get(course, 0) for course in clique)

    # Sort cliques by total number of advised students
    sorted_cliques = sorted(cliques, key=total_students_in_clique, reverse=True)

    return sorted_cliques

def sort_cliques_by_size(cliques):

    cliques.sort(key=len, reverse=True)

    return cliques

def sort_courses_in_clique(clique, df_course_details):
    # Create a mapping of course numbers to the chosen sorting criterion (e.g., number of advised students)
    course_sorting_criterion = df_course_details.set_index('CourseNo')['NumberOfAdvisedStudents'].to_dict()

    # Sort the courses in the clique based on the sorting criterion
    sorted_clique = sorted(clique, key=lambda course: course_sorting_criterion.get(course, 0))

    return sorted_clique

def generate_time_slots():
    """
    Generate a list of valid time slots for each day of the week.
    Exclude Tuesday 10:00-12:00.
    """
    # Define working hours and days
    start_time = datetime.time(8, 0)
    end_time = datetime.time(16, 0)
    days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
    
    # Generate time slots
    time_slots = []
    delta = datetime.timedelta(hours=1)
    for day in days_of_week:
        current_time = datetime.datetime.combine(datetime.date.today(), start_time)
        while current_time.time() <= end_time:  # Include the end time
            if not (day == 'Tuesday' and (current_time.time() > datetime.time(10, 0) and current_time.time() < datetime.time(12, 0))):  # Exclude until 12:00
                time_slots.append(f"{day} {current_time.strftime('%H:%M')}")
            current_time += delta
    return time_slots


def initialize_room_availability(df_rooms, time_slots):
    """
    Initialize a dictionary to track the availability of each room for each time slot.
    """
    room_availability = {row['RoomNo']: {time_slot: True for time_slot in time_slots} for _, row in df_rooms.iterrows()}
    return room_availability

def initialize_lecturer_availability(df_lecturer_prefs, time_slots):
    """
    Initialize a dictionary to track the availability of each lecturer for each time slot.
    """
    lecturer_availability = {row['FacultyID']: {time_slot: True for time_slot in time_slots} for _, row in df_lecturer_prefs.iterrows()}
    return lecturer_availability

def find_available_resources(course_info, room_availability, lecturer_availability, time_slots):
    """
    Find an available time slot, room, and lecturer for the course section.
    """
    # Example logic for finding resources (to be refined based on specific rules)
    for time_slot in time_slots:
        for room, available in room_availability.items():
            if available[time_slot] and room_matches_course(room, course_info):
                for lecturer, l_available in lecturer_availability.items():
                    if l_available[time_slot] and lecturer_prefers_course(lecturer, course_info):
                        return time_slot, room, lecturer
    return None, None, None

def schedule_course_section(timetable, course, section, time_slot, room, lecturer):
    """
    Schedule the course section in the timetable.
    """
    # Add the course section to the timetable
    timetable_key = (course, section)
    timetable[timetable_key] = {'time_slot': time_slot, 'room': room, 'lecturer': lecturer}

# def update_availability(room_availability, lecturer_availability, room, lecturer, time_slot):
#     """
#     Update the availability of the room and lecturer.
#     """
#     room_availability[room][time_slot] = False
#     lecturer_availability[lecturer][time_slot] = False

def update_availability(room_availability, lecturer_availability, room, lecturer, start_time_slot, session_length, time_slots):
    """
    Update the availability of the room and lecturer for the duration of the session.

    Args:
    room_availability (dict): A dictionary tracking the availability of rooms.
    lecturer_availability (dict): A dictionary tracking the availability of lecturers.
    room (str): The room identifier.
    lecturer (str): The lecturer identifier.
    start_time_slot (str): The starting time slot of the session.
    session_length (int): The length of the session in hours.
    time_slots (list): The list of all possible time slots.
    """
    start_index = time_slots.index(start_time_slot)
    for i in range(session_length):
        # Calculate the index for the current time slot
        current_index = start_index + i
        if current_index < len(time_slots):
            current_time_slot = time_slots[current_index]

            # Update availability for the room and lecturer at the current time slot
            room_availability[room][current_time_slot] = False
            lecturer_availability[lecturer][current_time_slot] = False


# Assuming df_rooms is a DataFrame with details about rooms, including their types

def room_matches_course(room, course_info, df_rooms):
    """
    Check if the room matches the course requirements.
    """
    required_room_type = course_info['RoomType']

    # Corrected check: Verify if the room is a key in the room_availability dictionary
    if room in df_rooms['RoomNo'].values:
        # Retrieve the type of the room from df_rooms DataFrame
        room_type = df_rooms[df_rooms['RoomNo'] == room]['Type'].iloc[0]
        return room_type == required_room_type

    # If the room is not found in df_rooms, return False
    return False


def lecturer_prefers_course(lecturer, course_info, lecturer_prefs):
    """
    Check if the lecturer prefers the course.

    Args:
    lecturer (str): The lecturer identifier.
    course_info (dict or DataFrame row): Information about the course, including course number.
    lecturer_prefs (DataFrame): A DataFrame containing lecturers' preferences.

    Returns:
    bool: True if the lecturer prefers the course, False otherwise.
    """
    # Retrieve the course number
    course_no = course_info['CourseNo']

    # Check if the lecturer is in the lecturer preferences DataFrame
    if lecturer in lecturer_prefs['FacultyID'].values:
        # Retrieve the lecturer's preferences
        lecturer_preference = lecturer_prefs[lecturer_prefs['FacultyID'] == lecturer].iloc[0]

        # Check if the course number is in any of the lecturer's preference columns
        for pref_col in ['Pref1', 'Pref2', 'Pref3', 'Pref4', 'Pref5']:
            if lecturer_preference[pref_col] == course_no:
                return True

    # If the course is not found in the lecturer's preferences or lecturer not in DataFrame, return False
    return False

# Step 4: Timetabling with Section, Room, and Lecturer Assignment

                                      
def find_available_resources_for_session(course_info, room_availability, lecturer_availability, time_slot, length, time_slots):
    """
    Find an available time slot, room, and lecturer for a specific session length.
    """
    for room in room_availability:
        if room_availability[room][time_slot] and room_matches_course(room, course_info, df_rooms):
            for lecturer in lecturer_availability:
                if lecturer_availability[lecturer][time_slot] and lecturer_prefers_course(lecturer, course_info, df_lecturer_prefs):
                    if check_availability_for_session_length(room, lecturer, room_availability, lecturer_availability, time_slot, length, time_slots):
                        return room, lecturer
    return None, None

def is_time_slot_suitable(start_time_slot, session_length, time_slots):
    """
    Check if the time slot is suitable for the session length.
    """
    # Extract the start day and time
    start_day, start_time = start_time_slot.split()
    start_hour, start_minute = map(int, start_time.split(':'))

    # Calculate the end time
    end_hour = start_hour + session_length
    end_time_slot = f"{start_day} {end_hour:02d}:{start_minute:02d}"

    # Check if the end time slot is within working hours and not on a restricted day/time
    if end_time_slot in time_slots and not is_restricted_time(start_day, start_hour, end_hour):
        return True
    return False

def is_restricted_time(day, start_hour, end_hour):
    """
    Check if the time slot falls into a restricted time.
    For example, Tuesday 10:00-12:00 is a common free slot.
    """
    # Define restricted times (e.g., Tuesday 10:00-12:00)
    if day == 'Tuesday' and ((start_hour <= 10 and end_hour > 10) or (start_hour < 12 and end_hour >= 12)):
        return True
    return False

def check_availability_for_session_length(room, lecturer, room_availability, lecturer_availability, start_time_slot, session_length, time_slots):
    """
    Check if the room and lecturer are available for the entire session length.
    """
    start_index = time_slots.index(start_time_slot)
    # Ensure the session doesn't overflow beyond available time slots
    if start_index + session_length - 1 >= len(time_slots):
        return False

    for i in range(session_length):
        # Calculate the index for the current time slot
        current_index = start_index + i
        current_time_slot = time_slots[current_index]

        # Check if the room and lecturer are available at this time slot
        if not room_availability[room][current_time_slot] or not lecturer_availability[lecturer][current_time_slot]:
            return False

    return True


# def schedule_course_sessions(course_info, room_availability, lecturer_availability, time_slots):
#     """
#     Schedule each session of a course section based on its contact hours.
#     """
#     sessions = []
#     contact_hours = course_info['ContactHours']

#     # Define session lengths based on contact hours
#     if contact_hours == 3:
#         session_lengths = [2, 1]
#     elif contact_hours == 4:
#         session_lengths = [2, 2]
#     elif contact_hours == 5:
#         session_lengths = [2, 2, 1]
#     elif contact_hours == 6:
#         session_lengths = [2, 2, 2]
#     else:
#         session_lengths = [contact_hours]  # For other cases

#     # Schedule each session
#     for length in session_lengths:
#         time_slot, room, lecturer = find_available_resources_for_session(course_info, room_availability, lecturer_availability, time_slots, length)
#         if time_slot and room and lecturer:
#             sessions.append({'time_slot': time_slot, 'room': room, 'lecturer': lecturer})
#             update_availability(room_availability, lecturer_availability, room, lecturer, time_slot)
#         else:
#             # Handle case where a suitable time slot, room, or lecturer is not found
#             # For simplicity, appending a session with 'None' values indicating the need for manual intervention
#             sessions.append({'time_slot': None, 'room': None, 'lecturer': None})

#     return sessions

# def schedule_course_sessions(course_info, room_availability, lecturer_availability, time_slots):
#     """
#     Schedule each session of a course section based on its contact hours.
#     """
#     # Validate course_info
#     if 'ContactHours' not in course_info:
#         raise ValueError("Missing 'ContactHours' in course_info")

#     sessions = []
#     contact_hours = course_info['ContactHours']

#     # Define session lengths based on contact hours
#     session_lengths = {
#         3: [2, 1],
#         4: [2, 2],
#         5: [2, 2, 1],
#         6: [2, 2, 2]
#     }.get(contact_hours, [contact_hours])  # Default to single session of full length

#     # Schedule each session
#     for i, length in enumerate(session_lengths, 1):
#         time_slot, room, lecturer = find_available_resources_for_session(course_info, room_availability, lecturer_availability, time_slots, length)
#         if time_slot and room and lecturer:

#             #print(time_slot, room, lecturer)
#             sessions.append({'time_slot': time_slot, 'room': room, 'lecturer': lecturer})
#             update_availability(room_availability, lecturer_availability, room, lecturer, time_slot)
#         else:
#             # More informative response for manual intervention
#             reason = "No suitable time slot/room/lecturer found"
#             sessions.append({'time_slot': None, 'room': None, 'lecturer': None, 'reason': reason, 'session_number': i})

#     return sessions


# def schedule_course_sessions(course_info, room_availability, lecturer_availability, time_slots):
#     """
#     Schedule each session of a course section based on its contact hours, ensuring sessions do not overlap.
#     """
#     sessions = []
#     contact_hours = course_info['ContactHours']
#     session_lengths = [2] * (contact_hours // 2) + ([1] if contact_hours % 2 else [])

#     scheduled_days = set()  # To track days on which sessions have been scheduled

#     for length in session_lengths:
#         session_scheduled = False
#         for time_slot in time_slots:
#             day, _ = time_slot.split()
#             if day in scheduled_days:
#                 continue  # Skip this time slot if a session has already been scheduled on this day

#             if is_time_slot_suitable(time_slot, length, time_slots):
#                 room, lecturer = find_available_resources_for_session(course_info, room_availability, lecturer_availability, time_slot, length, time_slots)
#                 if room and lecturer:
#                     sessions.append({'time_slot': time_slot, 'room': room, 'lecturer': lecturer})
#                     update_availability(room_availability, lecturer_availability, room, lecturer, time_slot, length, time_slots)
#                     scheduled_days.add(day)  # Mark this day as used
#                     session_scheduled = True
#                     break  # Break the loop to avoid scheduling another session on the same day

#         if not session_scheduled:
#             # If no suitable slot was found for this session, append a placeholder for manual intervention
#             sessions.append({'time_slot': None, 'room': None, 'lecturer': None, 'reason': 'Suitable time slot not found'})

#     return sessions

def schedule_course_sessions(course_info, room_availability, lecturer_availability, time_slots):
    """
    Schedule each session of a course section based on its contact hours, 
    ensuring sessions do not overlap and follow preferred day distributions.
    """
    sessions = []
    contact_hours = course_info['ContactHours']
    session_lengths = [2] * (contact_hours // 2) + ([1] if contact_hours % 2 else [])

    # Preferred session distributions
    preferred_distributions = {
        1: [('Sunday', ), ('Monday', ), ('Tuesday', ), ('Wednessday', ), ('Thursday', ) ],
        2: [('Sunday', 'Tuesday'), ('Monday', 'Wednesday'), ('Monday', 'Thursday'), ('Tuesday', 'Thursday')],
        3: [('Sunday', 'Tuesday', 'Thursday'), ('Monday', 'Wednesday', 'Thursday')]
    }

    # Get the preferred distribution for this course
    preferred_days = preferred_distributions.get(len(session_lengths), [])

    # Iterate through preferred day distributions
    for preferred_day_combo in preferred_days:
        session_scheduled = [False] * len(session_lengths)
        for i, length in enumerate(session_lengths):
            for time_slot in time_slots:
                day, _ = time_slot.split()
                if day != preferred_day_combo[i]:
                    continue  # Skip if not the preferred day for this session

                if is_time_slot_suitable(time_slot, length, time_slots):
                    room, lecturer = find_available_resources_for_session(course_info, room_availability, lecturer_availability, time_slot, length, time_slots)
                    if room and lecturer:
                        sessions.append({'time_slot': time_slot, 'room': room, 'lecturer': lecturer})
                        update_availability(room_availability, lecturer_availability, room, lecturer, time_slot, length, time_slots)
                        session_scheduled[i] = True
                        break  # Break after scheduling this session

        # Check if all sessions are scheduled successfully
        if all(session_scheduled):
            return sessions  # Return if all sessions are scheduled as per preferred distribution

    # If sessions could not be scheduled as per preferred days, append placeholders for manual intervention
    for i in range(len(session_lengths)):
        if not session_scheduled[i]:
            sessions.append({'time_slot': None, 'room': None, 'lecturer': None, 'reason': 'Suitable time slot not found on preferred day'})

    return sessions



def schedule_sections(sorted_cliques, df_course_details, df_rooms, df_lecturer_prefs):
    # Define time slots (excluding Tuesday 10:00-12:00)
    time_slots = generate_time_slots()

    # Initialize timetable and other necessary structures
    timetable = {}
    room_availability = initialize_room_availability(df_rooms, time_slots)
    lecturer_availability = initialize_lecturer_availability(df_lecturer_prefs, time_slots)

    # Iterate through each clique
    for clique in sorted_cliques:
        # Sort courses in the clique by the number of advised students (ascending order)
        sorted_courses = sort_courses_in_clique(clique, df_course_details)

        # Schedule each course
        for course in sorted_courses:

            print(course)
            # Check if the course is already scheduled
            if any(course == scheduled_course for scheduled_course, _ in timetable):
                print(f"{course} Already scheduled")
                continue

            # Fetch course details
            course_info = df_course_details[df_course_details['CourseNo'] == course].iloc[0]
            number_of_sections = course_info['NumberOfSections']

            # Schedule each section of the course
            for section in range(number_of_sections):
                sessions = schedule_course_sessions(course_info, room_availability, lecturer_availability, time_slots)
                timetable[(course, section)] = deepcopy(sessions)
            # break
        # break

    return timetable, room_availability, lecturer_availability, time_slots

# def schedule_sections(sorted_cliques, df_course_details, df_rooms, df_lecturer_prefs):
#     # Define time slots (excluding Tuesday 10:00-12:00)
#     time_slots = generate_time_slots()

#     # Initialize timetable and other necessary structures
#     timetable = {}
#     room_availability = initialize_room_availability(df_rooms, time_slots)
#     lecturer_availability = initialize_lecturer_availability(df_lecturer_prefs, time_slots)

#     # Iterate through each clique
#     for clique in sorted_cliques:
#         # Sort courses in the clique by the number of advised students (ascending order)
#         sorted_courses = sort_courses_in_clique(clique, df_course_details)

#         # Schedule each course
#         for course in sorted_courses:
#             # Fetch course details
#             print("+ " + course + " +")
#             course_info = df_course_details[df_course_details['CourseNo'] == course].iloc[0]
#             number_of_sections = course_info['NumberOfSections']
#             contact_hours = course_info['ContactHours']
#             room_type = course_info['RoomType']

#             # Schedule each section of the course
#             for section in range(number_of_sections):

#                 sessions = schedule_course_sessions(course_info, room_availability, lecturer_availability, time_slots)
#                 print(sessions)
#                 timetable[(course, section)] = deepcopy(sessions)
            

#     return timetable, room_availability, lecturer_availability, time_slots


# Step 5: Handling Unscheduled Courses and Sections
def handle_unscheduled_courses_and_sessions(timetable, df_course_details, room_availability, lecturer_availability, time_slots):
    """
    Schedule any remaining unscheduled courses and their sessions.
    """
    for index, course_info in df_course_details.iterrows():
        course_no = course_info['CourseNo']
        number_of_sections = course_info['NumberOfSections']
        number_of_sessions = course_info['NumberofSessions']

        for section in range(number_of_sections):
            # Check if this section of the course is already fully scheduled
            if (course_no, section) not in timetable or len([s for s in timetable[(course_no, section)] if s['time_slot'] is not None]) < number_of_sessions:
                # Schedule remaining sessions for this section
                remaining_sessions = schedule_course_sessions(course_info, room_availability, lecturer_availability, time_slots)
                if (course_no, section) in timetable:
                    # Replace any placeholder sessions with actual scheduled sessions
                    for i, session in enumerate(timetable[(course_no, section)]):
                        if session['time_slot'] is None and remaining_sessions:
                            timetable[(course_no, section)][i] = remaining_sessions.pop(0)
                    # Append any additional remaining sessions
                    timetable[(course_no, section)].extend(remaining_sessions)
                else:
                    timetable[(course_no, section)] = remaining_sessions

    return timetable

# def handle_unscheduled_courses_and_sessions(timetable, df_course_details, room_availability, lecturer_availability, time_slots):
#     """
#     Schedule any remaining unscheduled courses and their sessions.
#     """
#     for index, course_info in df_course_details.iterrows():
#         course_no = course_info['CourseNo']
#         number_of_sections = course_info['NumberOfSections']

#         for section in range(number_of_sections):
#             # Check if this section of the course is already fully scheduled
#             if (course_no, section) not in timetable or len(timetable[(course_no, section)]) < course_info['NumberofSessions']:
#                 # Schedule remaining sessions for this section
#                 remaining_sessions = schedule_course_sessions(course_info, room_availability, lecturer_availability, time_slots)
#                 if (course_no, section) in timetable:
#                     timetable[(course_no, section)].extend(remaining_sessions)
#                 else:
#                     timetable[(course_no, section)] = remaining_sessions

#     return timetable

# def handle_unscheduled_courses(timetable, df_course_details, room_availability, lecturer_availability, time_slots):
#     # Iterate through all courses in the course details
#     for index, course_info in df_course_details.iterrows():
#         course_no = course_info['CourseNo']
#         number_of_sections = course_info['NumberOfSections']

#         # Check if the course has already been scheduled in all its sections
#         scheduled_sections = sum(1 for key in timetable if key[0] == course_no)
#         if scheduled_sections < number_of_sections:
#             # Schedule remaining sections
#             for section in range(scheduled_sections, number_of_sections):
#                 # Find available resources
#                 time_slot, room, lecturer = find_available_resources(course_info, room_availability, lecturer_availability, time_slots)
#                 if time_slot and room and lecturer:
#                     # Schedule the course section
#                     schedule_course_section(timetable, course_no, section, time_slot, room, lecturer)
#                     update_availability(room_availability, lecturer_availability, room, lecturer, time_slot)

#     return timetable


# Step 6: Final Adjustments and Validation
def final_adjustments_and_validation(timetable, df_course_details, df_rooms, df_lecturer_prefs, time_slots):
    """
    Make final adjustments to the timetable and validate it, considering the sessions.
    """
    # Check for any conflicts or unmet constraints
    conflicts = check_for_conflicts_with_sessions(timetable, df_course_details, df_rooms, df_lecturer_prefs, time_slots)

    # If there are conflicts, attempt to resolve them
    if conflicts:
        resolve_conflicts_with_sessions(timetable, conflicts, df_course_details, df_rooms, df_lecturer_prefs, time_slots)

    # Validate that all courses and sessions have been scheduled
    validation_success = validate_complete_scheduling_with_sessions(timetable, df_course_details)

    return timetable, validation_success

def check_for_conflicts_with_sessions(timetable, df_course_details, df_rooms, df_lecturer_prefs, time_slots):
    """
    Check the timetable for any scheduling conflicts or unmet constraints, considering sessions.
    """
    conflicts = []
    # Check for overlapping sessions
    for (course, section), sessions in timetable.items():
        for session in sessions:
            time_slot = session['time_slot']
            room = session['room']
            lecturer = session['lecturer']

            # Check for room and lecturer availability conflicts
            if not is_room_available_for_session(room, df_rooms, time_slot) or \
               not is_lecturer_available_for_session(lecturer, df_lecturer_prefs, time_slot):
                conflicts.append({'course': course, 'section': section, 'time_slot': time_slot, 'room': room, 'lecturer': lecturer})

    return conflicts

def is_room_available_for_session(room, df_rooms, time_slot):
    """
    Check if the room is available for the given time slot.
    """
    # Assuming df_rooms has a column 'AvailableTimeSlots' which is a list of available time slots for each room
    room_data = df_rooms[df_rooms['RoomNo'] == room]

    if room_data.empty:
        # Room not found
        return False

    # Check if the time slot is in the room's list of available time slots
    available_time_slots = room_data.iloc[0]['AvailableTimeSlots']
    return time_slot in available_time_slots


def is_lecturer_available_for_session(lecturer, df_lecturer_prefs, time_slot):
    """
    Check if the lecturer is available for the given time slot.
    """
    # Assuming df_lecturer_prefs has a column 'AvailableTimeSlots' which is a list of available time slots for each lecturer
    lecturer_data = df_lecturer_prefs[df_lecturer_prefs['FacultyID'] == lecturer]

    if lecturer_data.empty:
        # Lecturer not found
        return False

    # Check if the time slot is in the lecturer's list of available time slots
    available_time_slots = lecturer_data.iloc[0]['AvailableTimeSlots']
    return time_slot in available_time_slots


def resolve_conflicts_with_sessions(timetable, conflicts, df_course_details, df_rooms, df_lecturer_prefs, time_slots):
    """
    Attempt to resolve any identified conflicts, considering sessions.
    """
    for conflict in conflicts:
        # Extract conflict details
        course_no, section, session = conflict['course'], conflict['section'], conflict['session']

        # Retrieve course and session info
        course_info = df_course_details[df_course_details['CourseNo'] == course_no].iloc[0]
        session_length = get_session_length(session, course_info)

        # Attempt to find alternative resources
        new_time_slot, new_room, new_lecturer = find_alternative_resources(course_info, df_rooms, df_lecturer_prefs, time_slots, session_length)

        if new_time_slot and new_room and new_lecturer:
            # Update the timetable with the new resources for the session
            update_timetable(timetable, course_no, section, session, new_time_slot, new_room, new_lecturer)
        else:
            # If no alternative resources found, flag for manual resolution
            flag_for_manual_resolution(course_no, section, session)

    return timetable

def get_session_length(session, course_info):
    """
    Determine the length of the session based on course information.
    """
    contact_hours = course_info['ContactHours']

    # Define session lengths based on contact hours
    if contact_hours == 3:
        # For a 3-hour course, split into 2-hour and 1-hour sessions
        return 2 if session == 1 else 1
    elif contact_hours == 4:
        # For a 4-hour course, two sessions of 2 hours each
        return 2
    elif contact_hours == 5:
        # For a 5-hour course, two 2-hour sessions and one 1-hour session
        return 2 if session in [1, 2] else 1
    elif contact_hours == 6:
        # For a 6-hour course, three sessions of 2 hours each
        return 2
    else:
        # For courses with other contact hours, assuming a single session of the entire duration
        return contact_hours

    return contact_hours


def find_alternative_resources(course_info, df_rooms, df_lecturer_prefs, time_slots, session_length):
    """
    Find alternative time slot, room, and lecturer for a session.
    """
    for time_slot in time_slots:
        # Check if the time slot is suitable for the session length
        if is_time_slot_suitable(time_slot, session_length, time_slots):
            for room in df_rooms['RoomNo']:
                if is_room_available_for_session(room, df_rooms, time_slot) and room_matches_course(room, course_info):
                    for lecturer in df_lecturer_prefs['FacultyID']:
                        if is_lecturer_available_for_session(lecturer, df_lecturer_prefs, time_slot) and lecturer_prefers_course(lecturer, course_info):
                            if check_availability_for_session_length(room, lecturer, df_rooms, df_lecturer_prefs, time_slot, session_length, time_slots):
                                return time_slot, room, lecturer
    return None, None, None

def update_timetable(timetable, course_no, section, session, new_time_slot, new_room, new_lecturer):
    """
    Update the timetable with new resources for a session.
    """
    # Update the timetable entry for this session
    timetable[(course_no, section)][session] = {'time_slot': new_time_slot, 'room': new_room, 'lecturer': new_lecturer}

def flag_for_manual_resolution(course_no, section, session, flagged_sessions):
    """
    Flag a session for manual resolution if no alternative resources are found.
    
    Args:
    course_no (str): The course number.
    section (int): The section number of the course.
    session (dict): A dictionary containing session details.
    flagged_sessions (list): A list to store details of flagged sessions.

    # Example usage
    flagged_sessions = []
    # Assuming you have a session that needs to be flagged
    session_example = {'time_slot': None, 'room': None, 'lecturer': None}
    flag_for_manual_resolution('CS101', 1, session_example, flagged_sessions)
    """
    # Add the session details to the flagged_sessions list
    flagged_session_info = {
        'CourseNo': course_no,
        'Section': section,
        'Session': session,
        'Reason': 'Unable to find suitable time slot, room, or lecturer'
    }
    flagged_sessions.append(flagged_session_info)


def validate_complete_scheduling_with_sessions(timetable, df_course_details):
    """
    Validate that all courses and their sessions have been scheduled.
    """
    for index, course_info in df_course_details.iterrows():
        course_no = course_info['CourseNo']
        number_of_sections = course_info['NumberOfSections']
        for section in range(number_of_sections):
            if (course_no, section) not in timetable or len(timetable[(course_no, section)]) < course_info['NumberofSessions']:
                return False  # Not all sessions have been scheduled
    return True

# Step 7: Output

def output_timetable_with_sessions(timetable, output_file_path):
    """
    Output the final timetable with session details to a CSV file.
    """
    # Prepare data for output
    output_data = []
    for (course, section), sessions in timetable.items():
        for session in sessions:
            output_data.append({
                'Course': course,
                'Section': section,
                'TimeSlot': session['time_slot'],
                'Room': session['room'],
                'Lecturer': session['lecturer']
            })

    # Create a DataFrame and write to CSV
    df_timetable = pd.DataFrame(output_data)
    df_timetable.to_csv(output_file_path, index=False)
    print(f"Timetable with sessions has been successfully saved to {output_file_path}")


# def output_timetable(timetable, output_file_path):
#     """
#     Output the final timetable to a CSV file.
#     """
#     # Convert the timetable dictionary to a list of dictionaries for easier DataFrame creation
#     timetable_list = []
#     for (course, section), info in timetable.items():
#         timetable_list.append({
#             'Course': course,
#             'Section': section,
#             'TimeSlot': info['time_slot'],
#             'Room': info['room'],
#             'Lecturer': info['lecturer']
#         })

#     # Create a DataFrame and write to CSV
#     df_timetable = pd.DataFrame(timetable_list)
#     df_timetable.to_csv(output_file_path, index=False)
#     print(f"Timetable has been successfully saved to {output_file_path}")


# Main execution
def main():
    # Main execution to load and preprocess data
    df_advised_courses, course_name_map, \
        course_room_map, course_details_map, \
            room_capacity_map, lecturer_prefs_map = load_and_preprocess_data()
    
    
    # construct the clash graph
    cliques = construct_graph_and_find_cliques(df_advised_courses)

    # sort the cliques by total enrollment
    sorted_cliques = sort_cliques_by_total_enrollment(cliques, df_course_details)

    # sorted_cliques = sort_cliques_by_size(cliques)

    # Function to format course info
    # def format_course(course_no):
    #    course_name = course_name_map.get(course_no, "Unknown Course")
    #    return f"{course_no}-{course_name}"

    # for i, clique in enumerate(sorted_cliques, start=1):
    #    formatted_clique = [format_course(course) for course in clique]
    #    student_counts = {course: df_advised_courses[df_advised_courses['CourseNo'] == course]['StudentNo'].nunique() for course in clique}
    #    print(f"Clique {i}: {student_counts}")

    timetable, room_availability, lecturer_availability, time_slots = schedule_sections(sorted_cliques, df_course_details, df_rooms, df_lecturer_prefs)
    
    # print(timetable)
    timetable = handle_unscheduled_courses_and_sessions(timetable, df_course_details, room_availability, lecturer_availability, time_slots)
   
    # final_adjustments_and_validation(timetable)
    # timetable, validation_success = final_adjustments_and_validation(timetable, df_course_details, df_rooms, df_lecturer_prefs, time_slots)
    
    # Specify the output file path
    output_file_path = 'final_timetable.csv'
    # Assuming timetable is already created and loaded
    output_timetable_with_sessions(timetable, output_file_path)

if __name__ == "__main__":
    main()
