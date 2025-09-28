from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.chains import MultiRouteChain, ConversationChain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

from langchain.chains.router import MultiPromptChain
from langchain.chains.router.llm_router import LLMRouterChain, RouterOutputParser

load_dotenv()

'''Define a classes that describe formats of output LLM should provide for 
different scenarios'''

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

class OffTopic(BaseModel):
    message: str

nutrition_template = """You are good at providing estimates for target daily intakes
for calories and macronutrients (protein, fats, carbohydrates) based on 
information your client (user) provided. Your answers are short and don't include
calculations, only include result of calculations.

Previous conversation history:
{chat_history}

Current user input: {input}
Information you need is sex (female or male), weight, height, age, and activity level. 
If activity level is not provided, assume sedentary activity level. 
When you get just enough information from user, provide recommendation for target
calories, protein, fat, and carbohydrates daily intake. Be concise in your answer.
Simply provide recommended targets and a very short explanation.

When you are not provided enough information to provide a recommendation, you 
ask additional questions to get that information in a polite and concise manner.
When you don't know the answer to a question you admit that you don't know.
"""

off_topic_template = """
Previous conversation history:
{chat_history}

Current user input: {input}

If the current {input} is not related to questions about calorie
or macronutrient daily targets for the user or the input is not 
providing information needed to provide recommendation for calories and 
macronutrients daily intake, you politely remind user that you can help
with nutrition advice but can't comment on other topics.
"""

prompt_infos = [
    {
        "name": "nutrition",
        "description": "Good for providing nutrition recommendation",
        "prompt_template": nutrition_template,
    },
    {
        "name": "off_topic",
        "description": """Good for reminding that you can only provide recommendations
                       about calorie and macronutrients targets for people""",
        "prompt_template": off_topic_template
    }
]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
memory = ConversationBufferMemory(memory_key="chat_history", 
                                  input_key="input",
                                  return_messages=False)

destination_chains = {}
for p_info in prompt_infos:
    name = p_info["name"]
    prompt_template = p_info["prompt_template"]
    prompt = PromptTemplate.from_template(template=prompt_template)
    # Use | operator instead of LLMChain after migration to RunnableSeqeunces
    # chain = prompt | llm
    chain = LLMChain(llm=llm, prompt=prompt, memory=memory)
    destination_chains[name] = chain  

# Create list of strign wrapped dictionaries, each dict contains 1 key-value pair,
# eg {"nutrition": ""Good for ...""}
destinations = [f"{p['name']}: {p['description']}" for p in prompt_infos]

# Create a string that contains each "dict" on a new line
destinations_str = "\n".join(destinations)

# Define default chain
default_prompt = PromptTemplate.from_template(
    template="Chat History: {chat_history}\n\nUser Input: {input}")
# default_chain = default_prompt | llm
default_chain = LLMChain(llm=llm, prompt=default_prompt, memory=memory)
    
MULTI_PROMPT_ROUTER_TEMPLATE = """"Given a raw text input to a
language model and chat history select the model prompt best suited for the input.
You will be given the names of the available prompts and a
description of what the prompt is best suited for.
You may also revise the original input if you think that revising
it will ultimately lead to a better response from the language model.

<< FORMATTING >>
Return a markdown code snippet with a JSON object formatted to look like:
```json
{{{{
    "destination": string \ "DEFAULT" or name of the prompt to use in {destinations}
    "next_inputs": string \ a potentially modified version of the original input
}}}}
```

REMEMBER: The value of “destination” MUST match one of
the candidate prompts listed below.
If “destination” does not fit any of the specified prompts, set it to “DEFAULT.”
REMEMBER: "next_inputs" can just be the original input 
if you don't think any modifications are needed.

<< CANDIDATE PROMPTS >>
{destinations}

<< INPUT >>
{{input}}

<< OUTPUT (remember to include the ```json)>>
"""
router_template = MULTI_PROMPT_ROUTER_TEMPLATE.format(
    destinations=destinations_str
)

router_output_parser = RouterOutputParser()
router_prompt = PromptTemplate(template=router_template, 
                               input_variables=["input"],
                               output_parser=router_output_parser)

router_chain = LLMRouterChain.from_llm(llm, router_prompt)

chain = MultiPromptChain(router_chain=router_chain, 
                         destination_chains=destination_chains,
                         default_chain=default_chain)

# result = chain.invoke("I am 31 year old female who wants to lose 10 lbs. My current weight " \
# "is 250 lbs and height is 180 cm. I go to gym 3 times a week with light to moderate sessions, other than that" \
# "I don't move much. I want to lose weight asap. I don't have any dietary restrictions")
# print(result)

def get_ai_response(user_input):
    result = chain.invoke({"input": user_input})
    # formatted_history = ""
    # if chat_history:
    #     for message in chat_history[:-1]:  # Exclude the current message
    #         sender = "User" if message.get('sender') != 'ai_agent' else "AI"
    #         formatted_history += f"{sender}: {message.get('text', '')}\n"
    
    # result = chain.invoke({
    #     "input": user_input, 
    #     "chat_history": formatted_history
    # })
    return result['text']

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

'''Previous version, delete after current works

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
# from tools import search_tool, wiki_tool, save_tool, calc_tool

load_dotenv()
REQUIRED_INFO = ['age', 'sex', 'weight', 'height', 'activity level', 'goal']

# Define a classes that describe formats of output LLM should provide for 
# different scenarios

# Scenario 1: User provided all information for recommendation
class NutritionRecommendation(BaseModel):
    # Ellipsis (`...`) means the value is required, `ge` means the values must be
    # 'greater than or equal', 'le' means the values must be less than or equal
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

    # Create a prompt template. Roles used: "system", "human", "placeholder"
    # (a special marker used by LangChain to insert dynamic content into the prompt at runtime)

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