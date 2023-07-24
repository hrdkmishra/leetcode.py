import click

from config_setup import (
    save_credentials_to_config,
    load_credentials_from_config,
    create_python_code_edit_file,
)
from function import (
    read_json_file,
    get_question_data_by_id,
    print_question_data,
    configure_api_instance,
    execute_graphql_query,
    get_question_content,
    html_to_text,
    fetch_code_content,
)


@click.command()
@click.option("--config", is_flag=True, help="Enter credentials and save to config")
@click.option(
    "--question",
    "-q",
    type=str,
    default="",
    help="Specify the question ID, title, or range (e.g., 10:20)",
)
@click.option(
    "--solve",
    "-s",
    type=int,
    help="Fetch the question content by ID and create a Python file for solving.",
)
def main(config, question, solve):
    leetcode_session, csrf_token = load_credentials_from_config()
    leetcode_db = read_json_file("leetcodeDb.json")

    if not leetcode_session or not csrf_token or config:
        leetcode_session = click.prompt("Enter your LeetCode session", type=str)
        csrf_token = click.prompt("Enter your CSRF token", type=str)
        save_credentials_to_config(leetcode_session, csrf_token)

    api_instance = configure_api_instance(csrf_token, leetcode_session)

    if solve:
        question_data = get_question_data_by_id(leetcode_db, str(solve))

        if question_data:
            title_slug = question_data["titleSlug"]
            content = get_question_content(api_instance, title_slug)
            print(f"https://leetcode.com/problems/{title_slug}/")
            print(html_to_text(content))

            python3_code = fetch_code_content(api_instance, title_slug)
            # Create the Python file with the Python3 code content
            if python3_code:
                create_python_code_edit_file(solve, title_slug, python3_code)
                print("Python file created successfully!")
            else:
                print(f"Python3 code not found for '{title_slug}'.")

        else:
            print(f"Question with ID '{solve}' not found.")

    elif not question:
        print("Please specify a question ID, title, or range with --qid option.")

    elif ":" in question:
        start, end = map(int, question.split(":"))
        questions_data = (
            leetcode_db.get("data", {})
            .get("problemsetQuestionList", {})
            .get("questions", [])
        )

        for i, question in enumerate(questions_data):
            question_id = question.get("frontendQuestionId")

            if start <= int(question_id) <= end:
                print_question_data(question)

    else:
        question_data = get_question_data_by_id(leetcode_db, question)

        if question_data:
            print_question_data(question_data)

        else:
            print(f"Question with ID '{question}' not found.")


if __name__ == "__main__":
    main() #tesr
