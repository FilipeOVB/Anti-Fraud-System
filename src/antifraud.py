import pandas as pd
import numpy as np

INPUT_PATH = "./data/transactional-sample.csv"
OUTPUT_PATH = "./data/transactional-result.csv"
CBK_DELAY_DAYS = 3

###################################################################################################################
# Detect if a User, Card ou Device has a CBK sequence in their history

# Example: The user 002 had a previously sequence of 2 CBKs
def has_cbk_seq(component_history)-> bool:

    if component_history.empty:
        return True

    if len(component_history) >= 2:

        component_history = component_history.copy()

        # Check if the component has 2 CBKs in sequence
        component_history["cbk_pair"] = component_history["has_cbk"] & component_history["has_cbk"].shift(1)

        if component_history["cbk_pair"].any():
            return False
        
    return True

###################################################################################################################
# Detect if a User, Card ou Device has more than 1 CBK in 7 days

def has_many_cbks(component_history, transaction, recent_days=7)-> bool:

    if component_history.empty:
        return True
    
    recent_window = transaction["transaction_date"] - pd.Timedelta(days=recent_days)
    recent_history = component_history[component_history["transaction_date"] >= recent_window]

    if int(recent_history["has_cbk"].sum()) > 1:
        return False

    return True

###################################################################################################################
# Detect if a User, Card or Device  attempts to make more than 3 transactions during the period

def has_many_transactions(component_history, transaction, hours=24, limit=3)-> bool:

    if component_history.empty:
        return True
    
    start_time = transaction["transaction_date"] - pd.Timedelta(hours=hours)
    short_period = component_history[(component_history["transaction_date"] >= start_time)]

    if len(short_period) >= limit:
        return False

    return True

###################################################################################################################
# Detect if a User, Card or Device reached the limit of CBKs in global history

def global_cbks(component_history, cbk_limit=5)-> bool:

    if component_history.empty:
        return True
    
    if int(component_history["has_cbk"].sum()) > cbk_limit:
        return False

    return True

###################################################################################################################
# Detect if a User, Card or Device has made transactions that exceed the amount_limit together

def has_exceeded_limit(transaction, previous, amount_limit = 1000, time_window_hours = 4)-> bool:

    start_time = transaction["transaction_date"] - pd.Timedelta(hours=time_window_hours)
    short_period = previous[(previous["transaction_date"] >= start_time)]
    
    #-------------------------------------------------------------------------------------------------------------#
    # Search for current component in the last 2 hours

    user = short_period[short_period["user_id"] == transaction["user_id"]]
    card = short_period[short_period["card_number"] == transaction["card_number"]]
    if pd.isna(transaction["device_id"]):
        device = pd.DataFrame()
    else:
        device = short_period[short_period["device_id"] == transaction["device_id"]]

    user_total = 0
    card_total = 0
    device_total = 0

    #-------------------------------------------------------------------------------------------------------------#
    # Total sum of each component

    if not user.empty:
        user_total = user["transaction_amount"].sum() + transaction["transaction_amount"]
    if not card.empty:
        card_total = card["transaction_amount"].sum() + transaction["transaction_amount"]
    if not device.empty:
        device_total = device["transaction_amount"].sum() + transaction["transaction_amount"]

    #-------------------------------------------------------------------------------------------------------------#

    if (user_total > amount_limit) or (card_total > amount_limit) or (device_total > amount_limit): 
        return False

    return True

###################################################################################################################
# Detect if the transaction exceed the limit value for this period

def too_late(transaction, high_value = 3500, start_period = 21, end_period = 4)-> bool:

    hour = transaction["transaction_date"].hour

    if transaction["transaction_amount"] >= high_value and ((hour >= start_period) or (hour <= end_period)):
        return False

    return True 

###################################################################################################################
# Detect if a User or Card or Device has changed its components many times in a period

# Example: User with many cards     - A user can only use 2 cards in 5 days
# Example: Device with many users   - A device can only have 3 users in 5 days
def has_component_rotation(main_component_history, previous_mt3d, transaction, component, recent_days=7, max_components= 2)-> bool:

    if main_component_history.empty:
        return True

    recent_window = transaction["transaction_date"] - pd.Timedelta(days=recent_days)
    recent_history = main_component_history[main_component_history["transaction_date"] >= recent_window]

    if recent_history.empty:
        return True
    
    recent_components = set(recent_history[component].dropna().unique())
    recent_components.add(transaction[component])

    cbk_components = previous_mt3d.loc[
            (previous_mt3d["has_cbk"]) & (previous_mt3d[component].isin(recent_components))][component].unique()
    
    if component == "card_number":
        if len(recent_components) >= max_components or len(cbk_components) >= 2:
            return False
        
    else:
        if len(recent_components) > max_components or len(cbk_components) >= 2:
            return False

    return True

###################################################################################################################

def analyzes_transaction(transaction, previous)-> bool:

    if previous.empty:
        return 0

    #=============================================================================================================#
    # Transaction history

    user_history = previous[previous["user_id"] == transaction["user_id"]]
    card_history = previous[previous["card_number"] == transaction["card_number"]]
    device_history = pd.DataFrame()

    if not pd.isna(transaction["device_id"]):
        device_history = previous[previous["device_id"] == transaction["device_id"]]

    #=============================================================================================================#
    # Transaction history with CBK info

    # Assuming we have the Chargeback information in 3 days (hypothetically)
    # Trasactions with more than 3 days
    previous_mt3d = previous[
        (previous["transaction_date"] <= transaction["transaction_date"] - pd.Timedelta(days=CBK_DELAY_DAYS))]

    merchant_history_cbk = pd.DataFrame()
    user_history_cbk = pd.DataFrame()
    card_history_cbk = pd.DataFrame()
    device_history_cbk = pd.DataFrame()

    if not previous_mt3d.empty:

        # Components history with more than 3 days
        merchant_history_cbk = previous_mt3d[previous_mt3d["merchant_id"] == transaction["merchant_id"]]
        user_history_cbk = previous_mt3d[previous_mt3d["user_id"] == transaction["user_id"]]
        card_history_cbk = previous_mt3d[previous_mt3d["card_number"] == transaction["card_number"]]
        device_history_cbk = pd.DataFrame()

        if not pd.isna(transaction["device_id"]):
            device_history_cbk = previous_mt3d[previous_mt3d["device_id"] == transaction["device_id"]]

    #=============================================================================================================#
    # Security cases

    # Case 1: two or more transactions that exceed the value limit in a period
    if not has_exceeded_limit(transaction, previous, amount_limit = 1000, time_window_hours = 4):
        return 1
    
    #---------------------------------------------------------------------------------------------------------#
    # Case 2: High value for the period
    if not too_late(transaction):
        return 2

    #---------------------------------------------------------------------------------------------------------#
    # Case 3: User made many transactions in a period
    if not has_many_transactions(user_history, transaction):
        return 3
    
    #---------------------------------------------------------------------------------------------------------#
    # Case 4: Card made many transactions in a period
    if not has_many_transactions(card_history, transaction):
        return 4
    
    #---------------------------------------------------------------------------------------------------------#
    # Case 5: Device made many transactions in a period
    if not has_many_transactions(device_history, transaction):
        return 5

    #---------------------------------------------------------------------------------------------------------#
    # Case 6: User with more than 1 CBK in 7 days
    if not has_many_cbks(user_history_cbk, transaction):
        return 6
    
    #---------------------------------------------------------------------------------------------------------#
    # Case 7: Card with more than 1 CBK in 7 days
    if not has_many_cbks(card_history_cbk, transaction):
        return 7
    
    #---------------------------------------------------------------------------------------------------------#
    # Case 8: Device with more than 1 CBK in 7 days
    if not has_many_cbks(device_history_cbk, transaction):
        return 8

    #---------------------------------------------------------------------------------------------------------#
    # Case 9: User with more than 5 CBK in their history
    if not global_cbks(user_history_cbk):
        return 9

    #---------------------------------------------------------------------------------------------------------#
    # Case 10: Card with more than 5 CBK in their history
    if not global_cbks(card_history_cbk):
        return 10

    #---------------------------------------------------------------------------------------------------------#
    # Case 11: Device with more than 5 CBK in their history
    if not global_cbks(device_history_cbk):
        return 11
    
    #---------------------------------------------------------------------------------------------------------#
    # Case 12: User with many cards
    u_many_cards = has_component_rotation(user_history, previous_mt3d, transaction, "card_number")
    if (not u_many_cards):
        return 12
    
    #---------------------------------------------------------------------------------------------------------#
    # Case 13: User with many devices
    u_many_devices = has_component_rotation(user_history, previous_mt3d, transaction, "device_id")
    if (not u_many_devices):
        return 13
    
    #---------------------------------------------------------------------------------------------------------#
    # Case 14: Card with many devices
    c_many_devices = has_component_rotation(card_history, previous_mt3d, transaction, "device_id")
    if (not c_many_devices):
        return 14

    #---------------------------------------------------------------------------------------------------------#
    # Case 15: Card with many users
    c_many_users = has_component_rotation(card_history, previous_mt3d, transaction, "user_id")
    if (not c_many_users):
        return 15
        
    #---------------------------------------------------------------------------------------------------------#
    # Case 16: Device with many users
    if not device_history.empty:
        d_many_users = has_component_rotation(device_history, previous_mt3d, transaction, "user_id")
        if (not d_many_users):
            return  16

    #---------------------------------------------------------------------------------------------------------#
    # Case 17: Device with many cards
    if not device_history.empty:
        d_many_cards = has_component_rotation(device_history, previous_mt3d, transaction, "card_number")
        if (not d_many_cards):
            return 17

    #---------------------------------------------------------------------------------------------------------#
    # Case 18: Merchant with more than 1 CBK in 7 days
    if not has_many_cbks(merchant_history_cbk, transaction):
        return 18
    
    #---------------------------------------------------------------------------------------------------------#
    
    # Transaction approved
    return 0

###################################################################################################################

def process_database():

    # Reading the spreadsheet
    df = pd.read_csv(INPUT_PATH, parse_dates=["transaction_date"])
    df = df.sort_values(by="transaction_date", ascending=True).reset_index(drop=True)

    # Converting CBK column from str to bool
    df["has_cbk"] = df["has_cbk"].astype(str).str.upper().map({"TRUE": True, "FALSE": False})
    # Replace blank device_id to Numpy NaN
    df["device_id"] = df["device_id"].replace("", np.nan)

    # Dataframe with the results
    historical = pd.DataFrame(columns=df.columns)
    historical = historical.astype(df.dtypes.to_dict())

    for i, transaction in df.iterrows():

        # Classifies a transaction based on history
        status = analyzes_transaction(transaction, historical)

        # status == 0 -> transaction approved
        # status != 0 -> in some cases the transaction was declined
        if status != 0:
            recommendation = "deny"
        else:
            recommendation = "approve"

        print(f"id: {i}\nrecommendation: {recommendation}")

        # Add columns to help with analysis
        transaction["recommendation"] = recommendation
        transaction["deny_case"] = status

        # Add the transaction to the history
        historical = pd.concat([historical, pd.DataFrame([transaction.copy()])], ignore_index=True)

    # Save the historical
    historical.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

