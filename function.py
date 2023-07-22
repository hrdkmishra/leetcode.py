import json
from bs4 import BeautifulSoup

from color import Colors


def process_api_response(api_response):
    if api_response.data:
        pass
    else:
        print("No data found in the API response.")


def read_json_file(file_path):
    with open(file_path, "r") as json_file:
        return json.load(json_file)


# # for graphql excution
# def execute_graphql_query(api_instance, graphql_query, query_variables):
#     graphql_request = leetcode.GraphqlQuery(query=graphql_query, variables=query_variables)
#     api_response = api_instance.graphql_post(body=graphql_request)
#     return api_response


# this is for print the question list in order


# for --solve
def get_question_content(api_instance, title_slug):
    graphql_query = "query questionContent($titleSlug: String!) { question(titleSlug: $titleSlug) { content } }"
    query_variables = {"titleSlug": title_slug}
    api_response = execute_graphql_query(api_instance, graphql_query, query_variables)
    content = api_response.data.question.content
    return content


def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    plain_text = soup.get_text()
    return plain_text


def fetch_code_content(api_instance, title_slug):
    graphql_query = """
    query questionEditorData($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        questionFrontendId
        codeSnippets {
          lang
          langSlug
          code
        }
      }
    }
    """

    query_variables = {
        "titleSlug": title_slug
    }

    api_response = execute_graphql_query(api_instance, graphql_query, query_variables)

    # if api_response and api_response.data and api_response.data.question:
    #     question_data = api_response.data.question
    #
    #     if question_data.code_snippets:
    #         code_snippets = question_data.code_snippets
    #         python3_snippet = next(
    #             (snippet for snippet in code_snippets if snippet.lang_slug == "python3"),
    #             None
    #         )
    #
    #         if python3_snippet:
    #             return python3_snippet

    python3_snippet = next(
        (snippet for snippet in api_response.data.question.code_snippets if snippet.lang_slug == "python3"),
        None
    )
    if python3_snippet:
        return python3_snippet

    return None
