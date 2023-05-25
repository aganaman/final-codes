#using nltk and spacy

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter
import spacy
import pandas as pd
from collections import Counter
from multiprocessing import Pool, freeze_support
import math
import time


# Load spaCy model and set up stop words
nlp = spacy.load("en_core_web_sm")
stop_words = nlp.Defaults.stop_words


# Set up stop words
stop_words = set(stopwords.words('english'))

# Define function to preprocess text
def preprocess(text):
    # Remove leading/trailing white space
    text = text.strip()

    # Convert to lowercase
    text = text.lower()

    # Replace newlines with spaces
    text = text.replace("\n", " ")

    # Tokenize text
    tokens = word_tokenize(text)

    # Remove stop words and punctuation
    tokens = [token for token in tokens if not token in stop_words and token.isalpha()]

    # Lemmatize tokens
    lemmatizer = nltk.WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    # Count the frequency of each token
    token_counts = Counter(tokens)

    # Return the most common tokens as a space-separated string
    return " ".join([token for token, count in token_counts.most_common(5)])


# Define function to calculate similarity score using spaCy
def calculate_similarity(args):
    change, testcase_docs, threshold = args
    doc2 = nlp(change)
    similarity_scores = [doc1.similarity(doc2) for doc1 in testcase_docs]
    matching_ids = [df_testcases.loc[i, "id"] for i, score in enumerate(similarity_scores) if score >= threshold[0] and score <= threshold[1]]
    #print(matching_ids)
    #print("----------------------------------------------------------------------------")
    return matching_ids


# Define batch size
batch_size = 200

# Load Excel files into pandas dataframes
df_testcases = pd.read_excel("C:/Users/namanaga/Downloads/gnr_ap_nlp/All_TCs.xlsx")
df_changes = pd.read_csv("C:/Users/namanaga/Downloads/gnr_ap_nlp/change_data.csv")



# Get number of batches needed
num_batches = math.ceil(len(df_testcases) / batch_size)

if __name__ == '__main__':
    start_time = time.time()

    print(df_testcases)
    print(df_changes)
    # Create a dictionary mapping each ID to its corresponding title
    id_to_title = dict(zip(df_testcases["id"], df_testcases["title"]))

    freeze_support()
    # Preprocess test case titles using multiprocessing
    with Pool() as pool:
        titles=[]
        for i in range(num_batches):
            # Get titles for current batch
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(df_testcases))
            try:
                testcase_titles = df_testcases["title"][start_idx:end_idx].tolist()

                # Process titles in current batch
                batch_results = pool.map(preprocess, testcase_titles)
                titles.extend(batch_results)

                # Print results for current batch
                print(f"Processed batch {i+1}/{num_batches}")
                #print("--------------------------testcase_titles--------------------------")
                #print(titles)
            
            except Exception as e:
                print(f"Error occurred: {e}")
                testcase_titles = df_testcases["title"][start_idx:end_idx].tolist()
        pool.close()
        pool.join()

    # Preprocess change descriptions
    change_descriptions = df_changes["Commit Description"].apply(preprocess)

    # Define threshold similarity score
    
    threshold = [0.75, 1]

    # Create a new column in the changes dataframe to store the similarity score
    #df_changes["similarity_score"] = 0
    #print("Assigning 0 to similarity score")
    #print(df_changes)

    # Use spaCy's nlp.pipe method to process all preprocessed test case titles at once
    testcase_docs = list(nlp.pipe(titles))


    print("Calling last pool for similarity score")
    # Calculate similarity scores for each change using multiprocessing
    with Pool() as pool:
        similarity_scores = pool.map(calculate_similarity, zip(change_descriptions, [testcase_docs] * len(change_descriptions), [threshold] * len(change_descriptions)))

    # Loop through each similarity score and print matching test
    # Loop through each similarity score and print matching test cases if above threshold
    print("--------------------------------------Printing similaroty scores-------------------------------------")
    print(similarity_scores)
    recommendations = [score for sublist in similarity_scores for score in sublist]

    #print("------similarity scores list-------------------------------")
    #print(similarity_scores)
    #for i, matching_ids in enumerate(similarity_scores):
    #    matching_id = df_testcases[df_testcases["title"]==matching_title]["id"].values[0]
    #    #print(f"Matching test case for change {i}: {matching_title} (ID: {matching_id}, similarity score: {max_similarity})")
    #    recommendations.append(df_testcases[df_testcases["title"]==matching_title]["id"].values[0])
    print("-----------------------recommendations-------------------------------------")
    unique_recommendations = list(set(recommendations))
    print(len(unique_recommendations))
    print(unique_recommendations)


    # Get recommended test case titles
    recommended_titles = [id_to_title[id] for id in unique_recommendations]

    print(len(unique_recommendations))
    print(len(recommended_titles))

    # Create DataFrame of recommendations with id and title columns
    df_recommendations = pd.DataFrame({
        "id": unique_recommendations,
        "title": recommended_titles
    })

    # Write DataFrame to Excel file
    df_recommendations.to_excel("C:/Users/namanaga/Downloads/gnr_ap_nlp/recommendations.xlsx", index=False)


    end_time = time.time()
    total_time = end_time - start_time
    print("Total time taken {0} seconds".format(total_time))
