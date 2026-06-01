import os
import pymongo
from datetime import datetime
from google import genai
from google.genai import types
import json

# ── CONNECTIONS ──
mongo_client = pymongo.MongoClient(os.environ["MONGODB_URI"])
db = mongo_client["accounting"]

gemini = genai.Client(
    vertexai=True,
    project="project-73b31b23-b6f9-4055-889",
    location="global"
)

# ── TOOL DEFINITION ──
query_tool = types.FunctionDeclaration(
    name="query_mongodb",
    description="Query the accounting database. Use this for any financial questions about transactions, invoices, charges, or customers.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "collection": types.Schema(
                type=types.Type.STRING,
                description="which collection to query: transactions, invoices, stripe_charges, stripe_customers"
            ),
            "filter": types.Schema(
                type=types.Type.OBJECT,
                description="mongodb filter object, use {} for all documents"
            ),
            "limit": types.Schema(
                type=types.Type.INTEGER,
                description="max number of results to return, default 10"
            )
        },
        required=["collection", "filter"]
    )
)

# ── ACTUAL TOOL FUNCTION ──
def query_mongodb(collection: str, filter: dict, limit: int = 10) -> list:
    try:
        results = list(db[collection].find(filter, {"_id": 0}).limit(limit))
        for doc in results:
            for key, val in doc.items():
                if isinstance(val, datetime):
                    doc[key] = val.strftime("%Y-%m-%d")
        return results
    except Exception as e:
        return [{"error": str(e)}]

# ── SYSTEM PROMPT ──
SYSTEM = """You are an accounting assistant for a small business.
You have access to a MongoDB database with these collections:
- transactions: expenses and income with vendor, amount, category, date, status
- invoices: bills sent to clients with amount, status (paid/unpaid/overdue), due_date
- stripe_charges: real payment data from Stripe with amount, customer_id, status
- stripe_customers: customer info from Stripe

Always use the query_mongodb tool to get real data before answering.
Never make up numbers. Be concise and clear."""

# ── THE AGENT LOOP ──
def ask(question: str) -> str:
    tools = types.Tool(function_declarations=[query_tool])

    messages = [
        types.Content(role="user", parts=[
            types.Part.from_text(SYSTEM + f"\n\nQuestion: {question}")
        ])
    ]

    while True:
        response = gemini.models.generate_content(
            model="gemini-3.5-flash",
            contents=messages,
            config=types.GenerateContentConfig(tools=[tools])
        )

        candidate = response.candidates[0]
        part = candidate.content.parts[0]

        # check if gemini wants to call a tool
        if hasattr(part, "function_call") and part.function_call:
            fn = part.function_call
            tool_args = dict(fn.args)

            print(f"  [calling {fn.name} with {tool_args}]")

            result = query_mongodb(
                collection=tool_args["collection"],
                filter=tool_args.get("filter", {}),
                limit=tool_args.get("limit", 10)
            )

            # append model response and tool result as proper Content objects
            messages.append(types.Content(
                role="model",
                parts=[part]
            ))
            messages.append(types.Content(
                role="user",
                parts=[types.Part.from_function_response(
                    name=fn.name,
                    response={"result": json.dumps(result, default=str)}
                )]
            ))

        else:
            return part.text

# ── INTERACTIVE CHAT ──
if __name__ == "__main__":
    print("Accounting Assistant ready. Type 'quit' to exit.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in ["quit", "exit"]:
            break
        if not question:
            continue
        print("\nAssistant: ", end="")
        answer = ask(question)
        print(answer)
        print()