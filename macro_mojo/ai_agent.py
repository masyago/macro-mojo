from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
# from tools import search_tool, wiki_tool, save_tool, calc_tool

load_dotenv()

'''Define a class that describes format of output LLM should provide
The class inherits from BaseModel'''
class NutritionResponse(BaseModel):
    calories: int
    protein: int
    fat: int
    carbs: int
    explanation: str
    source: list[str]
    tools_used: list[str]

def get_ai_response(query, session_history):
    llm = ChatOpenAI(model="gpt-4.1-mini")
    parser = PydanticOutputParser(pydantic_object=NutritionResponse)

    '''
    Create a prompt template. Roles used: "system", "human", "placeholder"
    (a special marker used by LangChain to insert dynamic content into the prompt at runtime)
    '''
    prompt = ChatPromptTemplate.from_messages(
            [
                ("system", 
                """You are a nutrition assisstant. You help people determine how 
                many calories and macronutrients to consume to reach their weight 
                goals. If physical activity levels are not provided, assume 
                sendetary daily activity.
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


