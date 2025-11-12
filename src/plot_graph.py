import pandas as pd
import matplotlib.pyplot as plt

def plot():

    # Reading the spreadsheet
    historical = pd.read_csv("./data/transactional-result.csv", parse_dates=["transaction_date"])

    case_descriptions = {
        1.0: "Case 1",
        2.0: "Case 2",
        3.0: "Case 3",
        4.0: "Case 4",
        5.0: "Case 5",
        6.0: "Case 6",
        7.0: "Case 7",
        8.0: "Case 8",
        9.0: "Case 9",
        10.0: "Case 10",
        11.0: "Case 11",
        12.0: "Case 12",
        13.0: "Case 13",
        14.0: "Case 14",
        15.0: "Case 15",
        16.0: "Case 16"
    }

    #---------------------------------------------------------------------------------------------------------#
    # Graph 1: Transactions with CBK

    cbk_counts = historical["has_cbk"].value_counts()
    plt.figure(figsize=(5, 4))

    ax = cbk_counts.plot(kind="bar", color=["#66b3ff", "#FFD580"], edgecolor="black")

    # Create graph
    plt.title("Transactions")
    plt.xlabel("CBK Status")
    plt.ylabel("Number of Transactions")
    plt.xticks([0, 1], ["Without CBK", "With CBK"], rotation=0)
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    # Adding labels
    for p in ax.patches:
        ax.annotate(f'{p.get_height()}',
                    (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='center',
                    xytext=(0, 5),
                    textcoords='offset points',
                    fontsize=10)

    plt.savefig("./data/graph-1-transactions.png", dpi=300, bbox_inches="tight")
    plt.show()

    #---------------------------------------------------------------------------------------------------------#
    # Graph 2: Transactions approved/denied

    rec_counts = historical["recommendation"].value_counts()
    plt.figure(figsize=(5, 4))

    ax = rec_counts.plot(kind="bar", color=["#4CAF50", "#F44336"], edgecolor="black")

    # Create graph
    plt.title("Approved vs Denied")
    plt.xlabel("Recommendation")
    plt.ylabel("Number of Transactions")
    plt.xticks([0, 1], ["Approved", "Denied"], rotation=0)
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    # Adding labels
    for p in ax.patches:
        ax.annotate(f'{p.get_height()}', 
                    (p.get_x() + p.get_width() / 2., p.get_height()), 
                    ha='center', va='center', 
                    xytext=(0, 5), 
                    textcoords='offset points',
                    fontsize=10)

    plt.savefig("./data/graph-2-apr-den.png", dpi=300, bbox_inches="tight")
    plt.show()

    #---------------------------------------------------------------------------------------------------------#
    # Graph 3: Hits and Misses
    
    # Finding hits and misses
    hit_cbk_denied = len(historical[(historical["has_cbk"] == True) 
                            & (historical["recommendation"] == "deny")])
    
    hit_legit_approved = len(historical[(historical["has_cbk"] == False) 
                            & (historical["recommendation"] == "approve")])
    
    miss_cbk_approved = len(historical[(historical["has_cbk"] == True) 
                            & (historical["recommendation"] == "approve")])
    
    miss_legit_denied = len(historical[(historical["has_cbk"] == False) 
                            & (historical["recommendation"] == "deny")])

    data = pd.Series({
        "Hit - Legit Approved": hit_legit_approved,
        "Hit - CBK Denied": hit_cbk_denied,
        "Miss - CBK Approved": miss_cbk_approved,
        "Miss - Legit Denied": miss_legit_denied
    })

    # Create graph
    plt.figure(figsize=(8, 5))
    colors = ["#4CAF50", "#81C784", "#E57373", "#F44336"]
    bars = data.plot(kind="bar", color=colors, edgecolor="black")
    plt.title("Hits and Misses", fontsize=14, fontweight="bold")
    plt.ylabel("Number of Transactions")
    plt.xticks(rotation=15, ha="right", fontsize=10)
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    # Adding labels
    for i, valor in enumerate(data):
        plt.text(i, valor + (max(data)*0.02), f"{valor}", ha="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    plt.savefig("./data/graph-3-hits-misses.png", dpi=300, bbox_inches="tight")
    plt.show()

    #---------------------------------------------------------------------------------------------------------#
    # Graph 4: 

    # Finding all denied transactions
    all_denies = historical[historical["recommendation"].str.lower() == "deny"].copy()

    # Count how many cases denied 
    legit_denied = all_denies[all_denies["has_cbk"] == False]["deny_case"].value_counts()
    cbk_denied   = all_denies[all_denies["has_cbk"] == True]["deny_case"].value_counts()

    # Combine the indexes
    cases = sorted(set(legit_denied.index).union(cbk_denied.index))
    df_cmp = pd.DataFrame({
        "Legit Denied": legit_denied.reindex(cases, fill_value=0),
        "CBK Denied": cbk_denied.reindex(cases, fill_value=0)
    })

    df_cmp.index = df_cmp.index.map(lambda x: case_descriptions.get(int(x), f"Case {x}"))

    # plot grouped bars
    ax = df_cmp.plot(kind="bar", figsize=(12, max(4, len(df_cmp) * 0.25)), edgecolor="black")
    plt.title("Case comparison: Legit Denied vs CBK Denied", fontsize=14, fontweight="bold")
    plt.ylabel("Number of Transactions")
    plt.xlabel("Case that denied")
    plt.xticks(rotation=0, ha="center")

    # Adding labels
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(f"{int(height)}", (p.get_x() + p.get_width() / 2, height),
                        ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.savefig("./data/graph-4-denied-cases.png", dpi=300, bbox_inches="tight")
    plt.show()

    #---------------------------------------------------------------------------------------------------------#
    # Graph 5: Distribution of approved CBKS 

    # Finding approved CBKs     (Misses)
    cbk_approved = historical[
        (historical["has_cbk"] == True) &
        (historical["recommendation"].str.lower() == "approve")
    ].copy()

    # Saving to spreadsheet for manual analysis 
    cbk_approved.to_csv("./data/cbk_approved_misses.csv", index=False)

    # Finding the first transaction of each user
    first_transaction = historical.groupby("user_id")["transaction_date"].min().reset_index()
    first_transaction.rename(columns={"transaction_date": "first_transaction_date"}, inplace=True)

    # Merging approved CBKs with First Transactions
    cbk_approved = cbk_approved.merge(first_transaction, on="user_id", how="left")

    # Check if the CBK aproved date is the same of a First Transaction of any user
    cbk_approved["is_first_transaction"] = (
        cbk_approved["transaction_date"] == cbk_approved["first_transaction_date"]
    )

    total_cbk_approved = len(cbk_approved)
    first_time_cbk = cbk_approved["is_first_transaction"].sum()
    recurring_cbk = total_cbk_approved - first_time_cbk

    # Graph info
    labels = ["1st Transaction (New User)", "Old User"]
    sizes = [first_time_cbk, recurring_cbk]
    colors = ["#ff9999","#66b3ff"]
    explode = (0.1, 0) 

    # Adding labels
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        sizes, explode=explode, labels=labels, colors=colors,
        autopct=lambda p: f"{p:.1f}%\n({int(p * total_cbk_approved / 100)})",
        startangle=140, textprops={'color':"black", 'fontsize': 11}
    )

    ax.set_title("Distribution of Approved CBKs\n(New Users vs Old Users)", fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig("./data/graph-5-cbk-users.png", dpi=300, bbox_inches="tight")
    plt.show()

    print("Graphs saved in: '/data'")
    #---------------------------------------------------------------------------------------------------------#


    