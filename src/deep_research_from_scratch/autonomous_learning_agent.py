
"""
Full Multi-Agent Research System

This module integrates all components of the research system:
- User clarification and scoping
- Research brief generation  
- Multi-agent research coordination
- Final report generation

The system orchestrates the complete research workflow from initial user
input through final report delivery.
"""

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from deep_research_from_scratch.utils import get_today_str
from deep_research_from_scratch.prompts import final_report_generation_prompt
from deep_research_from_scratch.state_scope import AgentState, AgentInputState
from deep_research_from_scratch.research_agent_scope import clarify_with_user, write_research_brief
from deep_research_from_scratch.multi_agent_supervisor import supervisor_agent

# ===== Config =====

from langchain.chat_models import init_chat_model
writer_model = init_chat_model("groq:llama3-8b-8192")

# ===== FINAL REPORT GENERATION =====

from deep_research_from_scratch.state_scope import AgentState

async def final_report_generation(state: AgentState):
    """
    Final report generation node.

    Synthesizes all research findings into a comprehensive final report
    """

    notes = state.get("notes", [])

    findings = "\n".join(notes)

    final_report_prompt = final_report_generation_prompt.format(
        research_brief=state.get("research_brief", ""),
        findings=findings,
        date=get_today_str()
    )

    final_report = await writer_model.ainvoke([HumanMessage(content=final_report_prompt)])

    return {
        "final_report": final_report.content, 
        "messages": ["Here is the final report: " + final_report.content],
    }

# ===== GRAPH CONSTRUCTION =====
# Build the overall workflow
deep_researcher_builder = StateGraph(AgentState, input_schema=AgentInputState)

# Add workflow nodes
deep_researcher_builder.add_node("clarify_with_user", clarify_with_user)
deep_researcher_builder.add_node("write_research_brief", write_research_brief)
deep_researcher_builder.add_node("supervisor_subgraph", supervisor_agent)
deep_researcher_builder.add_node("final_report_generation", final_report_generation)

# Add workflow edges
deep_researcher_builder.add_edge(START, "clarify_with_user")
deep_researcher_builder.add_edge("write_research_brief", "supervisor_subgraph")
deep_researcher_builder.add_edge("supervisor_subgraph", "final_report_generation")
deep_researcher_builder.add_edge("final_report_generation", END)

# Compile the full workflow
agent = deep_researcher_builder.compile()



import uuid
import operator
from typing import List, Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model

# --- 1. SETUP MODEL ---
# Ensure you have your API key set in env: GROQ_API_KEY
model = init_chat_model("groq:llama3-8b-8192")

# --- 2. DEFINE STATE SCHEMAS ---

class Checkpoint(TypedDict):
    id: str
    name: str
    objective: str
    # Content fields (populated by Node 2)
    study_material: str 
    quiz_questions: list[str]
    # User Interaction fields (populated by Node 3)
    user_answers: list[str]
    # Evaluation fields (populated by Node 4)
    score: int
    passed: bool
    feedback: str
    # Simplified teaching fields (populated by Node 5)
    simplified_material: str

class State(TypedDict):
    report: str
    user_request: str
    checkpoints: list[Checkpoint]
    current_checkpoint_index: int 

# --- 3. DEFINE PYDANTIC MODELS (LLM INTERFACE) ---

# Schema for Node 1 (Structure)
class CheckpointItem(BaseModel):
    name: str = Field(description="Name of the checkpoint")
    objective: str = Field(description="Objective of the checkpoint")

class CheckpointResponse(BaseModel):
    checkpoints: List[CheckpointItem]

# Schema for Node 2 (Content)
class CheckpointContent(BaseModel):
    study_material: str = Field(description="Brief study material (approx 100 words)")
    quiz_questions: List[str] = Field(description="Exactly 3 assessment questions")

# Schema for Node 4 (Evaluation)
class EvaluationResult(BaseModel):
    score: int = Field(description="Score out of 100")
    feedback: str = Field(description="Constructive feedback for the student")
    passed: bool = Field(description="True if score >= 70, False if failed")

# Schema for Node 5 (Simplified Teaching - Feynman Technique)
class SimplifiedContent(BaseModel):
    simplified_material: str = Field(description="Simple explanation using Feynman Technique (short, plain language, no jargon)")

# Create Structured LLMs
structure_gen = model.with_structured_output(CheckpointResponse)
content_gen = model.with_structured_output(CheckpointContent)
evaluator_gen = model.with_structured_output(EvaluationResult)
simplified_gen = model.with_structured_output(SimplifiedContent)


# --- 4. DEFINE NODES ---

def generate_structure(state: State):
    """Node 1: Breaks the report down into topics (No content yet)."""
    print("--- Generating Structure ---")
    report = state['report']
    response = structure_gen.invoke(f"Extract learning checkpoints from this report: {report}")
    
    clean_checkpoints = []
    for item in response.checkpoints:
        data = item.model_dump()
        # Initialize Defaults
        data['id'] = str(uuid.uuid4())
        data['study_material'] = ""
        data['quiz_questions'] = []
        data['user_answers'] = []
        data['score'] = 0
        data['passed'] = False
        data['feedback'] = ""
        data['simplified_material'] = ""
        
        clean_checkpoints.append(data)
        
    return {"checkpoints": clean_checkpoints, "current_checkpoint_index": 0}


def create_content(state: State):
    """Node 2: Generates study material and questions in PARALLEL (Batch)."""
    print("--- Creating Content (Batch) ---")
    report = state['report']
    user_req = state['user_request']
    checkpoints = state['checkpoints']
    
    # Prepare Batch Prompts
    prompts = []
    for cp in checkpoints:
        prompt = f"""You are creating educational content for a learning checkpoint.

Report Context: {report}
User Goal: {user_req}

Checkpoint Details:
- Name: {cp['name']}
- Objective: {cp['objective']}

REQUIREMENTS:
1. Create a clear, concise study material (approximately 100 words) that explains the key concepts of this checkpoint
2. Create EXACTLY 3 assessment questions that test understanding of the study material

IMPORTANT: Your response MUST include both fields:
- study_material: The explanation text
- quiz_questions: A list of exactly 3 questions (as strings)

Example format:
- study_material: "Python is a high-level programming language..."
- quiz_questions: ["What is X?", "Explain Y?", "How does Z work?"]

Now create the content:"""
        prompts.append(prompt)
    
    # Run Batch
    results = content_gen.batch(prompts)
    
    # Map back to state
    updated_checkpoints = []
    for cp, res in zip(checkpoints, results):
        cp['study_material'] = res.study_material
        cp['quiz_questions'] = res.quiz_questions
        updated_checkpoints.append(cp)
        
    return {"checkpoints": updated_checkpoints}


def administer_quiz(state: State):
    """Node 3: Pauses graph to show content and wait for user answers."""
    idx = state.get("current_checkpoint_index", 0)
    checkpoints = state["checkpoints"]
    
    if idx >= len(checkpoints):
        return {} # Safety catch

    current_cp = checkpoints[idx]
    
    print(f"--- Administering Quiz: {current_cp['name']} ---")

    # Use simplified material if available (after remediation), otherwise use original
    material = current_cp['simplified_material'] if current_cp['simplified_material'] else current_cp['study_material']

    # Prepare Payload for UI/User
    user_view = {
        "title": current_cp["name"],
        "material": material,
        "questions": current_cp["quiz_questions"]
    }

    # *** INTERRUPT ***
    # The graph STOPS here. Resume with: graph.invoke(Command(resume=answers_list))
    user_answers = interrupt(user_view)
    
    # Resume Logic
    current_cp["user_answers"] = user_answers
    checkpoints[idx] = current_cp
    
    return {"checkpoints": checkpoints}


def evaluate_submission(state: State):
    """Node 4: Grades the quiz and decides next steps."""
    print("--- Evaluating Submission ---")
    idx = state["current_checkpoint_index"]
    checkpoints = state["checkpoints"]
    current_cp = checkpoints[idx]
    
    # Evaluate
    prompt = f"""
    Topic: {current_cp['name']}
    Questions: {current_cp['quiz_questions']}
    Answers: {current_cp['user_answers']}
    Rubric: Pass mark is 70.
    """
    result = evaluator_gen.invoke(prompt)
    
    # Save Result
    current_cp["score"] = result.score
    current_cp["passed"] = result.passed
    current_cp["feedback"] = result.feedback
    checkpoints[idx] = current_cp
    
    # Decide Index Movement
    next_idx = idx
    if result.passed:
        print(f"PASSED ({result.score}). Moving to next topic.")
        next_idx = idx + 1
    else:
        print(f"FAILED ({result.score}). Retrying same topic.")
        # next_idx stays the same
        
    return {"checkpoints": checkpoints, "current_checkpoint_index": next_idx}


def simplified_teaching(state: State):
    """Node 5: Remedial teaching using Feynman Technique (Simple Explanations)."""
    print("--- Simplified Teaching Mode (Feynman Technique) ---")
    idx = state["current_checkpoint_index"]
    checkpoints = state["checkpoints"]
    current_cp = checkpoints[idx]
    
    # Create a Feynman-style explanation based on what the student struggled with
    prompt = f"""The student struggled with this topic. Use the FEYNMAN TECHNIQUE to create a MUCH SIMPLER explanation.
    
Topic: {current_cp['name']}
Original Explanation: {current_cp['study_material']}

Questions Asked:
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(current_cp['quiz_questions'])])}

Student's Answers:
{chr(10).join([f"{i+1}. {a}" for i, a in enumerate(current_cp['user_answers'])])}

Feedback on Their Answers: {current_cp['feedback']}

FEYNMAN TECHNIQUE RULES:
1. Use ONLY simple, everyday language - avoid all technical jargon
2. Explain as if talking to a 10-year-old
3. Use analogies and real-world examples
4. Break complex ideas into simple parts
5. Be very short and concise
6. Focus on the core concept the student got wrong

Create a simplified explanation that helps the student understand the concept:"""
    
    result = simplified_gen.invoke(prompt)
    
    # Save the simplified material
    current_cp["simplified_material"] = result.simplified_material
    checkpoints[idx] = current_cp
    
    print(f"Simplified material generated for retry")
    
    return {"checkpoints": checkpoints}


# --- 5. ROUTING LOGIC ---

def decide_next_step(state: State) -> Literal["administer_quiz", "simplified_teaching", END]:
    idx = state["current_checkpoint_index"]
    checkpoints = state["checkpoints"]
    
    # 1. Done?
    if idx >= len(checkpoints):
        print("--- All Checkpoints Completed ---")
        return END
        
    # 2. Failed? (Check current index status)
    current_cp = checkpoints[idx]
    # If we have a score but passed is False, we need help
    if "passed" in current_cp and current_cp["passed"] is False:
        return "simplified_teaching"
        
    # 3. Ready for Quiz (New topic or retry)
    return "administer_quiz"


# --- 6. BUILD GRAPH ---

builder = StateGraph(State)

# Add Nodes
builder.add_node("generate_structure", generate_structure)
builder.add_node("create_content", create_content)
builder.add_node("administer_quiz", administer_quiz)
builder.add_node("evaluate_submission", evaluate_submission)
builder.add_node("simplified_teaching", simplified_teaching)

# Add Edges
builder.add_edge(START, "generate_structure")
builder.add_edge("generate_structure", "create_content")
builder.add_edge("create_content", "administer_quiz") # Start 1st quiz
builder.add_edge("administer_quiz", "evaluate_submission")
builder.add_edge("simplified_teaching", "administer_quiz") # Retry loop

# Add Conditional Edge
builder.add_conditional_edges(
    "evaluate_submission",
    decide_next_step,
    {
        "administer_quiz": "administer_quiz",
        "simplified_teaching": "simplified_teaching",
        END: END
    }
)

learning_agent = builder.compile()

"""
State Definitions and Pydantic Schemas for Research Agent

This module defines the state objects and structured schemas used for
the research agent workflow, including researcher state management and output schemas.
"""

import operator
from typing_extensions import TypedDict, Annotated, List, Sequence
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# ===== STATE DEFINITIONS =====

class ResearcherState(TypedDict):
    """
    State for the research agent containing message history and research metadata.

    This state tracks the researcher's conversation, iteration count for limiting
    tool calls, the research topic being investigated, compressed findings,
    and raw research notes for detailed analysis.
    """
    researcher_messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_call_iterations: int
    research_topic: str
    compressed_research: str
    raw_notes: Annotated[List[str], operator.add]

class ResearcherOutputState(TypedDict):
    """
    Output state for the research agent containing final research results.

    This represents the final output of the research process with compressed
    research findings and all raw notes from the research process.
    """
    compressed_research: str
    raw_notes: Annotated[List[str], operator.add]
    researcher_messages: Annotated[Sequence[BaseMessage], add_messages]

# ===== STRUCTURED OUTPUT SCHEMAS =====

class ClarifyWithUser(BaseModel):
    """Schema for user clarification decisions during scoping phase."""
    need_clarification: bool = Field(
        description="Whether the user needs to be asked a clarifying question.",
    )
    question: str = Field(
        description="A question to ask the user to clarify the report scope",
    )
    verification: str = Field(
        description="Verify message that we will start research after the user has provided the necessary information.",
    )

class ResearchQuestion(BaseModel):
    """Schema for research brief generation."""
    research_brief: str = Field(
        description="A research question that will be used to guide the research.",
    )

class Summary(BaseModel):
    """Schema for webpage content summarization."""
    summary: str = Field(description="Concise summary of the webpage content")
    key_excerpts: str = Field(description="Important quotes and excerpts from the content")

