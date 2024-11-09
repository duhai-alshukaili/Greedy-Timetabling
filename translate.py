import pandas as pd
from googletrans import Translator, LANGUAGES

# Load your data file (change 'your_file.csv' to the path of your data file)
df = pd.read_csv('Names.csv')

# Initialize the translator
translator = Translator()

# Function to translate names
def translate_name(name):
    try:
        # Translate from Arabic to English
        return translator.translate(name, src='ar', dest='en').text
    except Exception as e:
        print(f"Error translating {name}: {e}")
        return name

# Apply translation to the 'Student Name (Arabic)' column
df['Name (EN)'] = df['Name'].apply(translate_name)

# Save the updated dataframe to a new file
df.to_csv('updated_Names.csv', index=False)
