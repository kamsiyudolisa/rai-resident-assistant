# RAI LLM setup

1. Put `ra_knowledge_base.csv` in this folder beside `app.py`.
2. Install the packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Create `.streamlit/secrets.toml` and add:

   ```toml
   OPENAI_API_KEY = "your-api-key"
   ```

4. Start the app:

   ```bash
   streamlit run app.py
   ```

5. Test it with: `My key is not working.`

The LLM selects a verified Entry ID. The answer, category, and urgency are
always copied from `ra_knowledge_base.csv`.
