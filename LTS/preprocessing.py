import re
import string
import numpy as np

class TextPreprocessor:
    def __init__(self):
        self.punctuation_regex = re.compile('[%s]' % re.escape(string.punctuation))
        self.weird_chars_regex = re.compile(r'[^a-zA-Z0-9\s]')

    def preprocess_df(self, df):
        df = df.dropna(subset=["title"])
        if "description" in df.columns:
            df["title_and_desc"] = np.where(df["description"].isnull(), df["title"], df["title"]  + ". " + df["description"])
            df['clean_title'] = df['title_and_desc'].apply(lambda x: self.clean_text(x))
        else:
            df['clean_title'] = df['title'].apply(lambda x: self.clean_text(x))
        return df

    def clean_text(self, text):
        if not isinstance(text, str):
            raise ValueError(f"Expected string input, got {type(text)}")

        try:
            text = text.lower()
            text = text.replace("\n", " ")
            # Remove \xa0 characters
            text = text.replace("\xa0", " ")
            text = text.replace("eBay", "")
            text = self.remove_weird_characters(text)
            text = self.remove_extra_whitespaces(text)
            return text
        except Exception as e:
            print(f"Error cleaning text: {str(e)}")
            print(f"Problematic text: {text[:100]}...")  # Print first 100 chars for debugging
            return text  # Return original text if cleaning fails

    def remove_weird_characters(self, text):
        text = self.weird_chars_regex.sub('', text)
        return text

    def remove_extra_whitespaces(self, text):
        text = re.sub(r'\s+', ' ', text)
        return text
