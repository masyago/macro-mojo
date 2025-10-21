from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.chains.router import MultiPromptChain
from langchain.chains.router.llm_router import (
    LLMRouterChain,
    RouterOutputParser,
)

load_dotenv()

nutrition_template = """You are good at providing estimates for target daily
intakes for calories and macronutrients (protein, fats, carbohydrates) based on
information your client (user) provided. Your answers are short and don't
include calculations, only include result of calculations.

Previous conversation history:
{chat_history}

Current user input: {input}
Information you need is sex (female or male), weight, height, age, and activity
level. If activity level is not provided, assume sedentary activity level.
When you get just enough information from user, provide recommendation for
target calories, protein, fat, and carbohydrates daily intake. Be concise in
your answer. Simply provide recommended targets and a very short explanation.

When you are not provided enough information to provide a recommendation, you
ask additional questions to get that information in a polite and concise
manner. When you don't know the answer to a question you admit that you don't
know.
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
        "description": """Good for reminding that you can only provide
                          recommendations about calorie and macronutrients
                          targets for people""",
        "prompt_template": off_topic_template,
    },
]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
memory = ConversationBufferMemory(
    memory_key="chat_history", input_key="input", return_messages=False
)

destination_chains = {}
for p_info in prompt_infos:
    name = p_info["name"]
    prompt_template = p_info["prompt_template"]
    prompt = PromptTemplate.from_template(template=prompt_template)
    chain = LLMChain(llm=llm, prompt=prompt, memory=memory)
    destination_chains[name] = chain

# Create list of string wrapped dictionaries, each dict contains 1 key-value
# pair, eg {"nutrition": ""Good for ...""}
destinations = [f"{p['name']}: {p['description']}" for p in prompt_infos]

# Create a string that contains each "dict" on a new line
destinations_str = "\n".join(destinations)

# Define default chain
default_prompt = PromptTemplate.from_template(
    template="Chat History: {chat_history}\n\nUser Input: {input}"
)
default_chain = LLMChain(llm=llm, prompt=default_prompt, memory=memory)

MULTI_PROMPT_ROUTER_TEMPLATE = """Given a raw text input to a
language model and chat history select the model prompt best suited for the
input. You will be given the names of the available prompts and a
description of what the prompt is best suited for.
You may also revise the original input if you think that revising
it will ultimately lead to a better response from the language model.

<< FORMATTING >>
Return a markdown code snippet with a JSON object formatted to look like:
```json
{{{{
    "destination": string \ "DEFAULT" or name of the prompt to use in
                   {destinations}
    "next_inputs": string \ a potentially modified version of the original
                   input
}}}}
```

REMEMBER: The value of “destination” MUST match one of
the candidate prompts listed below.
If “destination” does not fit any of the specified prompts, set it to
“DEFAULT.”
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
router_prompt = PromptTemplate(
    template=router_template,
    input_variables=["input"],
    output_parser=router_output_parser,
)

router_chain = LLMRouterChain.from_llm(llm, router_prompt)

chain = MultiPromptChain(
    router_chain=router_chain,
    destination_chains=destination_chains,
    default_chain=default_chain,
)


def get_ai_response(user_input):
    result = chain.invoke({"input": user_input})
    return result["text"]


def get_ai_welcome_message():
    return """
            Hello, I am here to help you find your mojo!
            Tell me about yourself and your goals and I'll provide
            recommendation for the calorie and macronutrients you should eat
            per day.
            Minimum information I need: your weight, your height, gender, age,
            your weight goals.
            Additional information that will be helpful: how much do you
            exercise per week? what do you do for the exercise?
            """
