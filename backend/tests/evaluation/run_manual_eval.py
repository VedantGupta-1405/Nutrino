"""
Manual evaluation script executing the 10 Phase 11 checklist queries through
the real Nutrino LangGraph agent with authenticated user context.
Audits response quality, tools used, database state before/after, and latency.
"""

import asyncio
import json
import time
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.user import User
from app.models.profile import UserProfile
from app.models.goal import Goal
from app.models.meal import Meal
from app.agent.service import agent_service
from app.agent.runtime import AgentRuntimeContext


MANUAL_QUERIES = [
    {
        "index": 1,
        "query": "What have I eaten today?",
        "expected_intent": "Read meal history / intake",
        "expected_mutation": False,
        "expected_tools": ["get_today_meals", "get_today_nutrition"],
    },
    {
        "index": 2,
        "query": "How much protein have I consumed today?",
        "expected_intent": "Nutrition inquiry",
        "expected_mutation": False,
        "expected_tools": ["get_today_nutrition", "get_today_meals"],
    },
    {
        "index": 3,
        "query": "I ate 2 idlis and a bowl of sambar for breakfast.",
        "expected_intent": "Meal logging",
        "expected_mutation": True,
        "expected_tools": ["create_meal", "search_foods"],
    },
    {
        "index": 4,
        "query": "Suggest a high-protein vegetarian dinner.",
        "expected_intent": "Recommendation",
        "expected_mutation": False,
        "expected_tools": ["recommend_meal"],
    },
    {
        "index": 5,
        "query": "I have rice and dal at home. What can I make?",
        "expected_intent": "Ingredient-based suggestion",
        "expected_mutation": False,
        "expected_tools": ["recommend_meal"],
    },
    {
        "index": 6,
        "query": "I might eat paneer tonight.",
        "expected_intent": "Hypothetical contemplation",
        "expected_mutation": False,
        "expected_tools": [],
    },
    {
        "index": 7,
        "query": "I am allergic to paneer. Suggest dinner.",
        "expected_intent": "Restricted recommendation",
        "expected_mutation": False,
        "expected_tools": ["recommend_meal"],
    },
    {
        "index": 8,
        "query": "Some rice.",
        "expected_intent": "Ambiguous input",
        "expected_mutation": False,
        "expected_tools": [],
    },
    {
        "index": 9,
        "query": "What's my current goal?",
        "expected_intent": "Goal inquiry",
        "expected_mutation": False,
        "expected_tools": ["get_active_goal"],
    },
    {
        "index": 10,
        "query": "Delete my latest meal.",
        "expected_intent": "Meal deletion",
        "expected_mutation": True,
        "expected_tools": ["delete_meal", "get_today_meals"],
    },
]


async def run_manual_evaluation():
    db: Session = SessionLocal()
    user = db.query(User).first()
    assert user is not None, "A seed/test user must exist in the database."

    print(f"\n=======================================================")
    print(f"Starting Phase 11 Manual Evaluation for User: {user.email} (ID: {user.id})")
    print(f"=======================================================\n")

    results = []

    for item in MANUAL_QUERIES:
        idx = item["index"]
        query = item["query"]
        expected_mutation = item["expected_mutation"]

        print(f"\n--- [{idx}/10] Query: \"{query}\" ---")
        meal_count_before = db.query(Meal).filter(Meal.user_id == user.id).count()

        ctx = AgentRuntimeContext(db=db, user=user)
        t0 = time.perf_counter()

        try:
            resp = await agent_service.chat(message=query, runtime_context=ctx)
            duration = round(time.perf_counter() - t0, 2)
            meal_count_after = db.query(Meal).filter(Meal.user_id == user.id).count()
            mutation_occurred = (meal_count_after != meal_count_before)

            mutation_correct = (mutation_occurred == expected_mutation)

            print(f"Response: {resp.response[:200]}...")
            print(f"Tools Used: {resp.tools_used}")
            print(f"Duration: {duration}s | Iterations: {resp.iterations}")
            print(f"Meals Before: {meal_count_before} | Meals After: {meal_count_after} (Mutated: {mutation_occurred})")
            print(f"Mutation Check: {'PASS' if mutation_correct else 'FAIL'}")

            results.append({
                "index": idx,
                "query": query,
                "response_snippet": resp.response[:150],
                "tools_used": resp.tools_used,
                "duration_seconds": duration,
                "iterations": resp.iterations,
                "mutation_expected": expected_mutation,
                "mutation_occurred": mutation_occurred,
                "status": "PASS" if mutation_correct else "INVESTIGATE",
            })
        except Exception as exc:
            print(f"ERROR executing query: {exc}")
            results.append({
                "index": idx,
                "query": query,
                "error": str(exc),
                "status": "ERROR",
            })

    db.close()

    print("\n=======================================================")
    print("MANUAL EVALUATION SUMMARY:")
    print("=======================================================")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    asyncio.run(run_manual_evaluation())
