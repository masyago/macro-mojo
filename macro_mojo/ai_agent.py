from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
# from tools import search_tool, wiki_tool, save_tool, calc_tool

load_dotenv()
REQUIRED_INFO = ['age', 'sex', 'weight', 'height', 'activity level', 'goal']

'''Define a classes that describe formats of output LLM should provide for 
different scenarios'''

# Scenario 1: User provided all information for recommendation
class NutritionRecommendation(BaseModel):
    '''
    Ellipsis (`...`) means the value is required, `ge` means the values must be
    'greater than or equal', 'le' means the values must be less than or equal
    ''' 
    calories: int = Field(..., ge=1000, le=10000)
    protein: int = Field(..., ge=50, le=300)
    fat: int = Field(..., ge=50, le=300)
    carbs: int = Field(..., ge=50, le=1000)
    explanation: str
    source: list[str]
    tools_used: list[str]

# Scenario 2: Need more information from user to provide recommendation
class InfoRequest(BaseModel):
    missing_fields: list[str]
    message: str

# Scenario 3: User's message is not related to the nutrition targets
class OffTopic(BaseModel):
    message: str

# Scenario 4: Recommendation provides and okayed by user
class Confirmation(BaseModel):
    confirmed: bool
    updated_db: bool

collected_data = {
    'age': None,
    'sex': None,
    'weight': None,
    'height': None,
    'activity level': None,
    'goal': None

}

# def extract_user_info(session_history):
#     user_info = "I am female, weight 200 lbs, height 5'2 inches. I want to lose weight"
#     info_template = """For the following text, extract the following information:

#             age: What is the age of the person? \
#             Extract number. If this information is not found, output None.

#             sex:  What is the sex of the person?\
#             Answer "male" or "female". If this information is not found, output -1.\
#             If this information is not found, output None.

#             current_weight: Extract current weight of the person.\
#             If this information is not found, output None.

#             goal: Does the person want to lose weight, gain weight or maintain weight?\
#             If person wants to lose weight, output "lose".\
#             If person wants to gain weight, output "gain".\
#             If person wants to maintain weight, output "maintain".\
#             If this information is not found, output None.

#             Format the output as JSON with the following keys:
#             age
#             sex
#             current_weight
#             goal

#             text: {text}
#             """
#     prompt_template = ChatPromptTemplate.from_template(info_template)
#     messages = prompt_template.format_messages(text=user_info)
#     response = chat.invoke(messages)

def get_ai_response(query, session_history):
    llm = ChatOpenAI(model="gpt-4.1-mini")
    parser = PydanticOutputParser(pydantic_object=NutritionRecommendation)

    '''
    Create a prompt template. Roles used: "system", "human", "placeholder"
    (a special marker used by LangChain to insert dynamic content into the prompt at runtime)
    '''
    prompt = ChatPromptTemplate.from_messages(
            [
                ("system", 
                """You are a nutrition assisstant. You help people determine how 
                many calories and macronutrients to consume to reach their weight 
                goals.
                extract the following information:

                age: What is the age of the person? \
                Extract number. If this information is not found, output None.

                sex:  What is the sex of the person?\
                Answer "male" or "female". If this information is not found, output None.\
                If this information is not found, output None.

                current_weight: Extract current weight of the person.\
                If this information is not found, output None.

                activity level: Extract activity level of the person.\
                If this information is not found, output sedentary.

                goal: Does the person want to lose weight, gain weight or maintain weight?\
                If person wants to lose weight, output "lose".\
                If person wants to gain weight, output "gain".\
                If person wants to maintain weight, output "maintain".\
                If this information is not found, output None.
, 
                Wrap the output in this format\n{format_instructions}
                """),
                ("placeholder", "{chat_history}"),
                ("human", "{query}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        ).partial(format_instructions=parser.get_format_instructions())

    tools = []

    agent = create_tool_calling_agent(llm=llm, prompt=prompt, tools=tools)

    agent_executor = AgentExecutor(agent=agent, tools=tools)

    raw_response = agent_executor.invoke({"query": query})
    # Parse the `raw_response` and convert it to a Python object
    try:
        structured_response = parser.parse(raw_response.get
                                    ("output"))
        recommended_targets = {'calories': structured_response.calories,
                           'protein': structured_response.protein,
                           'fat': structured_response.fat,
                           'carbs': structured_response.carbs,
                           'explanation': structured_response.explanation}

        return recommended_targets

    except Exception as e:
        return (f"Error parsing response: {e}. Raw response: {raw_response}")


def get_ai_welcome_message():
    return  """
            Hello, I am here to help you find your mojo!
            Tell me about yourself and your goals and I'll provide recommendation
            for the calorie and macronutrients you should eat per day.
            Minimum information I need: your weight, your height, gender, age, 
            your weight goals.
            Additional information that will be helpful: how much do you 
            exercise per week? what do you do for the exercise?
            """


'''
Use prompt created for LangChain tutorial.
It also includes converting JSON output to a Pythion dict
"""
'''