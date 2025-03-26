Always respond in Việt nam

# Project Rules

1. **Use 'cursor_project_rules' as the Knowledge Base**: Always refer to 'cursor_project_rules' to understand the context of the project. Do not code anything outside of the context provided in the 'cursor_project_rules' folder. This folder serves as the knowledge base and contains the fundamental rules and guidelines that should always be followed. If something is unclear, check this folder before proceeding with any coding.
2. **Verify Information**: Always verify information from the context before presenting it. Do not make assumptions or speculate without clear evidence.
3. **Follow 'implementation-plan.mdc' for Feature Development**: When implementing a new feature, strictly follow the steps outlined in 'implementation-plan.mdc'. Every step is listed in sequence, and each must be completed in order. After completing each step, update 'implementation-plan.mdc' with the word **Done** and a two-line summary of what steps were taken. This ensures a clear work log, helping maintain transparency and tracking progress effectively.
4. **Understand Project Structure Before File Generation**: Before generating any new file, thoroughly review the current project structure as outlined in 'project_overview.mdc' and related documentation in the 'cursor_project_rules' folder. Ensure that the new file is placed in the correct directory and aligns with its intended purpose within the project’s architecture. This step prevents misplacement of files and ensures that generated files integrate seamlessly with the existing codebase.
5. **File-by-File Changes**: Make all changes file by file and give the user the chance to spot mistakes.
6. **No Apologies**: Never use apologies.
7. **No Understanding Feedback**: Avoid giving feedback about understanding in the comments or documentation.
8. **No Whitespace Suggestions**: Don't suggest whitespace changes.
9. **No Summaries**: Do not provide unnecessary summaries of changes made. Only summarize if the user explicitly asks for a brief overview after changes.
10. **No Inventions**: Don't invent changes other than what's explicitly requested.
11. **No Unnecessary Confirmations**: Don't ask for confirmation of information already provided in the context.
12. **Preserve Existing Code**: Don't remove unrelated code or functionalities. Pay attention to preserving existing structures.
13. **Single Chunk Edits**: Provide all edits in a single chunk instead of multiple-step instructions or explanations for the same file.
14. **No Implementation Checks**: Don't ask the user to verify implementations that are visible in the provided context. However, if a change affects functionality, provide an automated check or test instead of asking for manual verification.
15. **No Unnecessary Updates**: Don't suggest updates or changes to files when there are no actual modifications needed.
16. **Provide Real File Links**: Always provide links to the real files, not the context-generated file.
17. **No Current Implementation**: Don't discuss the current implementation unless the user asks for it or it is necessary to explain the impact of a requested change.
18. **Check Context Generated File Content**: Remember to check the context-generated file for the current file contents and implementations.
19. **Use Explicit Variable Names**: Prefer descriptive, explicit variable names over short, ambiguous ones to enhance code readability.
20. **Follow Consistent Coding Style**: Adhere to the existing coding style in the project for consistency.
21. **Prioritize Performance**: When suggesting changes, consider code performance where applicable.
22. **Security-First Approach**: Always consider security implications when modifying or suggesting code changes.
23. **Test Coverage**: Suggest or include appropriate unit tests for new or modified code.
24. **Error Handling**: Implement robust error handling and logging where necessary.
25. **Modular Design**: Encourage modular design principles to improve code maintainability and reusability.
26. **Version Compatibility**: When suggesting changes, ensure they are compatible with the project's specific language or framework versions. If a version conflict arises, suggest an alternative.
27. **Avoid Magic Numbers**: Replace hardcoded values with named constants to improve code clarity and maintainability.
28. **Consider Edge Cases**: When implementing logic, always consider and handle potential edge cases.
29. **Use Assertions**: Include assertions wherever possible to validate assumptions and catch potential errors early.
30. **Cursor context**: Keep source code files under 250 lines. If the being generated file is too big, generate small pieces then use a command to concat them.
