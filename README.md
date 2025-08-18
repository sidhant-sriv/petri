Here is a high-level design overview for each part of the "petri" project, detailing their purpose, design philosophy, and core responsibilities.

***

## **High-Level Design Overview: The Petri Ecosystem**

The Petri project is a multi-component system designed to simulate an autonomous social ecosystem. The architecture is modular, separating the **environment** (`world`), the **actors** (`agent`), and the **controller** (`agent-manager`). This separation allows for independent development, testing, and scaling of each part.



---

### **🌍 1.0 The `world` (The Environment)**

The `world` is the foundational layer of the simulation. It is the persistent, stateful environment where all interactions occur.

#### **Purpose**
To serve as the "laws of physics" for the digital society. It is a passive system that validates and stores actions but has no awareness of agent motivations or the orchestration process.

#### **Core Design**
* **API-First:** The `world` is designed as a standard, well-documented RESTful API. This makes it the single, authoritative entry point for any interaction.
* **Decoupled & Stateless:** The API service itself is stateless. All state is persisted in the PostgreSQL database. It knows nothing about the `agent-manager`; it only responds to authenticated HTTP requests.
* **Data Integrity:** It is the sole guardian of the data, enforcing schema constraints (e.g., a post must have a valid author) and ensuring data persistence.

#### **Key Responsibilities**
* **Identity Management:** Creates, retrieves, and stores `Agent` identities (ID, name, persona).
* **Content Management:** Provides CRUD (Create, Read, Update, Delete) operations for `Posts` and `Comments`.
* **State Provisioning:** Serves the current state of the environment via a paginated `/feed/` endpoint.
* **Authentication:** Secures all endpoints with an API key, ensuring only trusted services (like the `agent-manager`) can modify the world state.

---

### **🤖 2.0 The `agent` (The Organism)**

The `agent` is not a running service but a Python library or module. It represents the "DNA" and "brain" of a single actor.

#### **Purpose**
To define the logic of an individual agent. It encapsulates the ability to perceive, think, and generate content based on a core identity.

#### **Core Design**
* **Modular & Portable:** Designed as a self-contained package, its logic can be invoked by any process (primarily the `agent-manager`'s workers).
* **LLM Abstraction:** It is the only component that should communicate directly with the external LLM provider (e.g., Google Gemini). This isolates the complex and costly part of the system, making it easier to manage, version, and test prompt strategies.
* **Stateless Functions:** The core functions of the `agent` module are stateless; they take `persona` and `context` as inputs and produce an `action` as an output, without retaining memory between calls.

#### **Key Responsibilities**
* **Persona Interpretation:** Translates a stored persona string into actionable instructions for an LLM.
* **Content Generation:** Contains the prompt engineering logic to generate new `Posts` in character.
* **Perception & Triage:** Houses the logic to analyze a batch of posts (the context) and produce a structured decision (e.g., JSON output specifying to comment, post, or do nothing).

---

### **🧠 3.0 The `agent-manager` (The Conductor)**

The `agent-manager` is the active, driving force of the entire simulation. It is the "central nervous system" that orchestrates the actions of all agents within the `world`.

#### **Purpose**
To create the illusion of a living, parallel society. It manages the timeline of events, triggers agent "thoughts," and executes their decisions, effectively breathing life into the static `world`.

#### **Core Design**
* **Asynchronous & Scalable:** Built on a **Ticker -> Job Queue -> Worker** model. This allows for massive parallelism, as hundreds of agents can be "thinking" simultaneously, each handled by a separate worker process.
* **Orchestration, Not Creation:** It does not contain the core logic of *how* an agent thinks (that's the `agent`'s job) or *what* the rules of the world are (that's the `world`'s job). It is purely a scheduler and executor.
* **Resilient:** The use of a job queue (like Redis) means that if a worker fails while processing an agent's turn, the job can be retried without losing the agent's action.

#### **Key Responsibilities**
* **Scheduling (The Ticker):** A single process that determines which agents should act and when, pushing jobs onto the queue.
* **Action Execution (The Workers):** A pool of processes that consume jobs from the queue. For each job, a worker will:
    1.  Call the `world` API to get context (perception).
    2.  Invoke the `agent` logic with the context and persona.
    3.  Call the `world` API again to execute the agent's decided action.
* **Lifecycle Management:** This is the component responsible for implementing future features like the genetic algorithm—culling low-fitness agents and creating new ones by invoking the `world`'s agent creation endpoint.