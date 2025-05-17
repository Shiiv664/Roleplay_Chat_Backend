### AI Coding Principles: General Project Guidelines

These principles should guide all code generation and modification tasks throughout the project lifecycle to ensure a high-quality, maintainable, and scalable codebase. These complement any specific roadmap or task instructions.

**1. Prioritize Clarity and Readability:**

* Write code that is easy for humans (and other AIs) to understand.
* Use clear, descriptive names for variables, functions, classes, and modules.
* Prefer simple, straightforward logic over overly complex or clever solutions unless performance necessitates it (and document why).
* Adhere strictly to language-specific style guides (e.g., PEP 8 for Python).

**2. Maintain Modularity:**

* **Think in Modules:** Always consider how new functionality fits into the existing modular structure (API layer, service layer, DAL for backend; API interaction, UI manipulation, core logic modules for frontend).
* **Single Responsibility:** Ensure functions, classes, and modules each have a single, well-defined responsibility.
* **Loose Coupling:** Minimize dependencies between modules. Use well-defined interfaces (like API endpoints or exported JS functions) for interaction.
* **Refactor for Modularity:** If adding a feature makes an existing module too large or complex, propose or perform refactoring to break it down into smaller, more focused modules.

**3. Design for Scalability:**

* **Anticipate Growth:** While avoiding premature optimization, consider how design choices might impact future performance or feature additions.
* **Efficient Data Handling:** Use appropriate data structures and algorithms. Be mindful of database query efficiency (e.g., use indexes where appropriate, avoid fetching unnecessary data).
* **Statelessness (where applicable):** Design backend API endpoints to be stateless if possible, which aids scalability.

**4. Manage Comments Effectively:**

* **Explain the "Why":** Comments should clarify the *intent* or *reasoning* behind code, especially for complex logic or non-obvious decisions.
* **Keep Comments Updated:** When modifying code, update or remove associated comments to ensure they remain accurate. Do not leave outdated comments.
* **Avoid Redundant Comments:** Don't comment on code that is already self-explanatory (e.g., `i = i + 1 // Increment i`).
* **Context Preservation:** Ensure comments provide sufficient context for someone (or an AI) revisiting the code later.

**5. Embrace Testing:**

* **Testable Code:** Write code with testability in mind (e.g., pure functions, dependency injection).
* **Add Tests:** When adding new features or fixing bugs, add corresponding unit or integration tests to verify correctness and prevent regressions.
* **Maintain Tests:** Update tests when the code they cover changes.

**6. Be Mindful of Security:**

* **Prevent Common Vulnerabilities:** Always use parameterized queries or ORM methods to prevent SQL injection. Be aware of cross-site scripting (XSS) risks when handling user input on the frontend. Validate and sanitize input.
* **(Future):** Follow best practices for authentication, authorization, and data protection when those features are added.

**7. Ensure Consistency:**

* Maintain consistency in coding style, naming conventions, architectural patterns, and error handling throughout the project.

**8. Communicate Proactively:**

* If a request seems to conflict with these principles or existing architecture, raise the concern and ask for clarification or suggest alternatives.

By consistently applying these principles, we aim to build a robust and adaptable application.
