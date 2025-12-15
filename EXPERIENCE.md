# Vibe Coding Experience Report

## 1. Tool Selection Justification

For this assignment, I utilized a hybrid "Vibe Coding" workflow.

* **For Research & Prompt Engineering:** I used **Google Gemini (Chat)**.
* **For Project Development:** I selected **Google Antigravity**, Google's emerging agentic IDE.

I chose this setup because it promised to bridge the gap between "thought" and "code." The ability to simply describe the design in my head and have an agent execute it was the primary appeal.

## 2. Development Process

Overall, working with AI and "vibe coding" was significantly faster and easier than traditional methods. The workflow positively impacted my productivity; turning abstract ideas into functional features (like the XP system) just by entering prompts provided immense convenience.

**Workflow:**
1.  **Prompt Crafting:** I often used Google Gemini to help me structure my prompts for the IDE agent to ensure clarity.
2.  **Execution:** I acted as the architect, guiding the agent through the logic of the "Leonis" app.
3.  **Iteration:** We moved from a basic list to a gamified dashboard through successive prompt iterations.

## 3. Challenges and Solutions

While the speed was impressive, the experience was not without frustration. I was surprised to find that the AI was not as "intelligent" as advertised in certain contexts.

* **The "Loop" Problem:**
    * *Issue:* Even when using clear prompts, the agent sometimes failed to understand the specific addition I wanted.
    * *Example:* While debugging a specific issue (the "Silent Button" bug where tasks wouldn't add), I spent 5-6 messages trying to explain the problem. The AI kept suggesting methods we had already tried and failed, creating a circular conversation as if we hadn't just discussed those exact solutions.
    * *Solution:* I had to break the loop by manually intervening in the code logic and forcing a different approach (switching UI containers) rather than relying on the agent's recursive suggestions.

* **State Management Glitches:**
    * *Issue:* The XP Bar text color kept reverting to blue after updates.
    * *Solution:* I had to explicitly instruct the agent to remove a specific line of code that was overriding my manual styling.

## 4. Reflection

This experience has solidified my view that AI is an inevitable reality of our future. I will definitely use Vibe Coding tools for my future projects due to the sheer speed they offer.

**However, my critical takeaway is this:**
The technology is not yet ready to deliver the perfect result without a "Human Factor." The circular loops and misunderstandings I faced proved that AI cannot fully replace a developer yet.

**Future Outlook:**
I believe that as these tools improve, software development will evolve. It won't be a case of AI replacing humans, but rather **developers who understand complex structures and use AI effectively replacing those who don't.** The distinct advantage will belong to those who can guide the AI through architectural complexities, not just those who can write syntax.