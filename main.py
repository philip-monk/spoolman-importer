# from main.py
...
    parser.add_argument(
        "action",
        choices=["create", "delete", "replace"], # 'replace' is correctly listed here
        help="Action to perform: 'create' to add new data, 'delete' to remove all data, 'replace' to do a full delete and then create."
    )
...
