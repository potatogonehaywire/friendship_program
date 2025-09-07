#pairing algorithm for the Cent Connect Program using a excel file taken from the survey
import pandas as pd
import os

def sort(file):
    """reads excel file and sorts users by grade"""
    #read excel file and convert to DataFrame
    data = pd.read_excel(file)

    #inplace=True changes data without =, drop=False keeps ID
    data.set_index("ID", inplace=True, drop=False)

    #rename columns
    data.columns = ["ID","Start","Completion","Email","Name","Modified","PreferredName","Grade","Gender","SameGender","Pronouns","Interests"\
                    ,"Language","Preference","InterestDesc","Profile","Avoid","Comments"]

    #if someone submitted multiple responses, remove their old response row, only keeping the newest row
    # data.drop_duplicates(subset=["Email"], keep="last", inplace=True)

    #splits interests and language into strings so we don't have to later
    data["Interests"] = data["Interests"].str.split(";")
    data["Language"] = data["Language"].str.split(";")

    #sort users by grade and put them in new DataFrames
    grade9_10 = data[(data["Grade"].isin([9,10]))]      #using [()] returns the whole row instead of just a boolean
    grade10_11 = data[(data["Grade"].isin([10, 11]))]
    grade11_12 = data[(data["Grade"].isin([11, 12]))]

    print("Sorting all users into separate grades...\n")

    demo = list(data["ID"].values[-1:]) + list(data["PreferredName"].values[-1:])

    return grade9_10, grade10_11, grade11_12, data, demo


def similarities(weight_inte, weight_lang, friend, person):
    """adds points when person and friend match interests or languages"""

    #initialize friend_pt
    friend_pt = 0

    #loop through interests
    for interest in friend.Interests:
        if interest in person.Interests:
            friend_pt += weight_inte

    #loop through languages, but only if both languages are lists and not an empty spot
    if isinstance(friend.Language, list) and isinstance(person.Language, list):
        for lang in friend.Language:
            if lang in person.Language:
                friend_pt += weight_lang
    
    return friend_pt


def rank(grade, demo):
    """each user in the grade ranks their potential friend with points"""

    #initialize final ranked dictionary
    all_ranked = {}

    #loop through each person, converted to named tuples
    for person in grade.itertuples():
        
        if str(person.ID) == str(demo[0]):

            friends_ranked = {}
            
            friends_show = {}

            c_grade = grade[(grade["ID"] != person.ID)]

            if person.SameGender == "Yes":
                c_grade = c_grade[(c_grade["Gender"] == person.Gender)]
                print(person.PreferredName + " picked same gender, removing all users with different genders")
            
            for friend in c_grade.itertuples():
                match person.Preference:
                    case "a friend with the same interests":
                        friends_show[friend.PreferredName] = similarities(2, 1.5, friend, person)
                    case "a friend with the same language":
                        friends_show[friend.PreferredName] = similarities(1, 3, friend, person)
                    case _:
                        friends_show[friend.PreferredName] = similarities(1.5, 2, friend, person)
            
            print(person.PreferredName + " has rated all their friends on similarity!\n" + str(friends_show) + "\n")

            for friend in c_grade.itertuples():
                match person.Preference:
                    case "a friend with the same interests":
                        friends_ranked[friend.ID] = similarities(2, 1.5, friend, person)
                    case "a friend with the same language":
                        friends_ranked[friend.ID] = similarities(1, 3, friend, person)
                    case _:
                        friends_ranked[friend.ID] = similarities(1.5, 2, friend, person)

            all_ranked[person.ID] = friends_ranked
        else:
            #initialize each person's ranked friends dictionary
            friends_ranked = {}

            #remove person from grade by making a copy with only users that don't have the person's ID
            c_grade = grade[(grade["ID"] != person.ID)]

            #remake dictionary with only users with the same gender if they want same gender options
            if person.SameGender == "Yes":
                c_grade = c_grade[(c_grade["Gender"] == person.Gender)]
            
            #loop through each friend, converted to named tuples
            for friend in c_grade.itertuples():
                #match person's interests/language preference with the right points
                match person.Preference:
                    case "a friend with the same interests":
                        #add friend's ID as key and add friend's score as value to friends_ranked
                        friends_ranked[friend.ID] = similarities(2, 1.5, friend, person)
                    case "a friend with the same language":
                        friends_ranked[friend.ID] = similarities(1, 3, friend, person)
                    case _:
                        friends_ranked[friend.ID] = similarities(1.5, 2, friend, person)
            
            #add friends_ranked to all_ranked
            all_ranked[person.ID] = friends_ranked

    return all_ranked


def pairing(preference):
    """uses a variant of the gale-shapley algorithm to match the best possible pairs"""
    #initialize everyone as free
    unpaired = list(preference.keys())
    #initialize proposals dictionary with people as keys and an empty list as value
    proposals = {person: [] for person in preference.keys()}
    #initialize matches dictionary to store pairs
    matches = {}

    #while unpaired isn't empty
    while unpaired:
        #pop one person as proposer
        proposer = unpaired.pop(0)
        proposer_pref = preference[proposer]

        #for each person in proposer's friends
        for preferred in proposer_pref:
            #if preferred has not already been proposed to by proposer
            if preferred not in proposals[proposer]:
                #record that preferred as been proposed to
                proposals[proposer].append(preferred)

                #skip to next preferred person if proposer is not in preferred's list
                if proposer not in preference[preferred]:

                    continue

                #if preferred has not been matched, match proposer with preferred and stop looking for next preferred person
                elif preferred not in matches:
                    #remove preferred from unpaired so they don't look for someone to pair with
                    unpaired.remove(preferred)
                    matches[preferred] = proposer
                    matches[proposer] = preferred
                    break

                else:
                    #find person preferred is matched with
                    current_match = matches[preferred]
                    # if current match is worse than proposer
                    if preference[preferred].index(proposer) < preference[preferred].index(current_match):

                        #add preferred and proposer as a pair
                        matches[preferred] = proposer
                        matches[proposer] = preferred
                        #kick person preferred was matched with out of matched
                        if current_match in matches.keys():
                            del matches[current_match]
                        #add formerly matched person to unpaired
                        unpaired.append(current_match)
                        break
    #remove duplicates by ordering the keys and values where key is less than value, so any duplicates are easily detected and removed
    final_matches = {key:val for key, val in matches.items() if key < val}
    return final_matches


def main(filename):
    #initialize dictionaries
    sorted_combined = {}
    ranked_combined = {}

    grade9_10, grade10_11, grade11_12, data_all, demo = sort(filename)

    #rank users in different grades
    ranked9_10 = rank(grade9_10, demo)
    ranked10_11 = rank(grade10_11, demo)
    ranked11_12 = rank(grade11_12, demo)

    #loop through all grade dictionaries
    for dictionary in (ranked9_10, ranked10_11, ranked11_12):
        #for each person and their ranked friends, add them to ranked_combined, updating the friends if person is already in the dictionary
        for person, friends in dictionary.items():
            if person not in ranked_combined:
                ranked_combined[person] = friends.copy()
            else:
                ranked_combined[person].update(friends)

    #sort everyone's friend pool from high to low score
    for person in ranked_combined.keys():
        #use sorted() to sort their friend pool, reverse = True so high score is first, turn output into a dictionary
        person_sorted = dict(sorted(ranked_combined[person].items(), key = lambda x: x[1], reverse = True))
        #initialize empty list to store everyone's friends
        person_pref = []
        person_show = []
        # add each friend to list to list
        for friend in person_sorted.keys():
            person_pref.append(friend)
            if person == demo[0]:
                person_show.append(str(data_all.at[friend, "PreferredName"]))

        if person == demo[0]:
            print(demo[1] + " has ranked all their friends from most to least similar: " + str(person_show) + "\n")

        sorted_combined[person] = person_pref

    #all paired users
    paired = pairing(sorted_combined)

    print("pairing up the most similar users...\n")

    #condition: if ID is a value in paired
    sort_by = data_all["ID"].isin(paired.values())

    #put all rows that don't fulfill condition into data_keys
    data_keys = data_all.loc[~sort_by].reset_index(drop=True)
    #put all rows that do fulfill condition into data_values
    data_values = data_all.loc[sort_by].reset_index(drop=True)

    #create new row for data_values to store their friend's ID
    data_values["IDFriend"] = ""

    #set data_values' index to ID, not removing original ID column, this lets us easily know who is in what row
    data_values.set_index("ID", inplace=True, drop=False)
    #set data_keys' index to ID, not removing original ID column, inplace = True directly changes data_values
    data_keys.set_index("ID", inplace=True, drop=False)

    #for each person in data_values
    for person, friend in paired.items():
        #set value of "IDFriend" to their friend's ID, uses their own ID to find where they are in the dataframe
        data_values.at[friend, "IDFriend"] = person
    #set their friend's ID as their index, this lets us join the dataframes nicely based off of one ID for each pair
    data_values.set_index("IDFriend", inplace=True)

    #rename all columns in data_values so the final dataframe doesn't have 2 columns with the same name
    data_values.columns = ["FID","FStart","FCompletion","FEmail","FName","FModified","FPreferredName","FGrade","FGender","FSameGender",\
                           "FPronouns","FInterests","FLanguage","FPreference","FInterestDesc","FProfile","FAvoid","FComments"]

    #concatenate the two dataframes, using the ID of people in data_keys as index
    data_paired = pd.concat([data_keys, data_values], axis=1).reindex(data_keys.index)

    #intialize MatchingInterests and MatchingLanguage columns
    data_paired["MatchingInterests"] = ""
    data_paired["MatchingLanguage"] = ""

    #look through each pair 
    for person in paired.keys():
        #if an interest matches, add interest to MatchingInterests
        for interest in data_paired.loc[person, "Interests"]:
            if interest in data_paired.loc[person,"FInterests"]:
                data_paired.loc[person, "MatchingInterests"] += interest
                data_paired.loc[person, "MatchingInterests"] += ", "
        
        #if both language sections are lists
        if isinstance(data_paired.loc[person, "Language"], list) and \
            isinstance(data_paired.loc[person, "FLanguage"], list): 

            #if a language matches, add language to MatchingLanguage  
            for language in data_paired.loc[person, "Language"]:
                if language in data_paired.loc[person,"FLanguage"]:
                    data_paired.loc[person, "MatchingLanguage"] += language
                    data_paired.loc[person, "MatchingLanguage"] += ", "

    #change MatchingInterests to be index
    data_paired.set_index("MatchingInterests", inplace=True)
    #pop MatchingLanguage and insert to the front
    Languages = data_paired.pop("MatchingLanguage")
    data_paired.insert(0, "MatchingLanguage", Languages)

    print("Done!")

    #output excel file
    data_paired.to_excel("output.xlsx")

    os.system("output.xlsx")


main("CentConnect_round1.xlsx")