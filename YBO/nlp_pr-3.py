
import spacy
import pandas as pd
from collections import Counter
from multiprocessing import Pool, freeze_support
import multiprocessing as mp

import math

# Load spaCy model and set up stop words
nlp = spacy.load("en_core_web_sm")
stop_words = nlp.Defaults.stop_words
# Define function to preprocess text
def preprocess(texts):
    # Load spaCy model and set up stop words
    nlp = spacy.load("en_core_web_sm")
    stop_words = nlp.Defaults.stop_words

    # Process texts using spaCy
    docs = nlp.pipe(texts, batch_size=1000, n_process=-1)

    # Generate preprocessed tokens for each document
    preprocessed_tokens = (
        " ".join(
            token.lemma_
            for token in doc
            if not token.is_stop and not token.is_punct
        )
        for doc in docs
    )

    # Generate top tokens for each document
    top_tokens = (
        (token for token, count in Counter(tokens).most_common(6))
        for tokens in preprocessed_tokens
    )

    # Join top tokens for each document into a single string
    preprocessed_texts = [" ".join(tokens) for tokens in top_tokens]

    return preprocessed_texts

# Define function to calculate similarity score using spaCy
def calculate_similarity(args):
    change, testcase_docs, threshold = args
    doc2 = nlp(change)
    similarity_scores = [doc1.similarity(doc2) for doc1 in testcase_docs]
    matching_ids = [df_testcases.loc[i, "id"] for i, score in enumerate(similarity_scores) if score >= threshold]
    #print(matching_ids)
    #print("----------------------------------------------------------------------------")
    return matching_ids


# Define batch size
batch_size = 200

# Load Excel files into pandas dataframes
df_testcases = pd.read_excel("C:/Users/namanaga/Downloads/rpl-s nlp test 6/All_TCs.xlsx")
df_changes = pd.read_csv("C:/Users/namanaga/Downloads/rpl-s nlp test 6/change_wise_recommendation.csv")



# Get number of batches needed
num_batches = math.ceil(len(df_testcases) / batch_size)

if __name__ == '__main__':
    print(df_testcases)
    print(df_changes)
    freeze_support()

    # Preprocess test case titles using multiprocessing
    mp.set_start_method('spawn')
    with Pool(processes=2, maxtasksperchild=1) as pool:
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
                print("--------------------------testcase_titles--------------------------")
                print(titles)
            
            except Exception as e:
                print(f"Error occurred: {e}")
                testcase_titles = df_testcases["title"][start_idx:end_idx].tolist()
        pool.close()
        pool.join()

    # Preprocess change descriptions
    change_descriptions = df_changes["Change Details"].apply(preprocess)

    # Define threshold similarity score
    threshold = 0.8

    # Create a new column in the changes dataframe to store the similarity score
    df_changes["similarity_score"] = 0
    print("Assigning 0 to similarity score")
    print(df_changes)

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
    print(len(set(recommendations)))
    print(set(recommendations))
