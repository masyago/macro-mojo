OVERVIEW
Calorie Tracker is a simple application for tracking calories and associated meals.
The application keeps track of calories and macronutrients (protein, fat, and carbohydrates)
user consumes during the day. It calculates how much user ate that day and how much 
calories and macronutrients left based on set daily targets.
Nutrition entries and meals can be added, edited, and deleted.
When creating a new nutrition entry or editing an existing one, user can select
only one meal or snack from a drop down menu.  
Targets can be edited. Only one set of targets is allowed per user.
All macronutrients displayed in grams.
For more information see 'APP PAGES DESCRIPTION' below.

THE APP WAS DEVELOPED AND RAN USING:
Make sure that you have installed Python, Poetry, PostgreSQL, command-line interface (CLI),
and a Google Chrome browser.

- Back-end: Python version 3.13.0
- Dependencies manager: Poetry version 2.0.1
- RDBMS: PostgreSQL version 17.4
- Browser: Google Chrome version 138.0.7204.169 (Official Build) (arm64)
- Command line: Visual Studio Code (VS Code) command-line interface version 1.102.2 (arm64)

INSTALL DEPENDENCIES
In terminal, run the command to install dependencies needed to run the app:
    `poetry install`

UPLOAD DATA
- Create a database `cal_tracker`. 
   - To do that: From a terminal, run command `createdb cal_tracker`
- Import file with schema to the database by running the following command in terminal:
    - `psql -d cal_tracker < schema.sql`
- Import file with data to the database by running the following command in terminal:
    - `psql -d cal_tracker < data.sql`

RUN THE APP
- To initialize the application, run the command in your terminal:
   `poetry run python app.py`
- Open a new tab in a browser and type URL: `http://localhost:5003/`.
- Login (See login credentials below)

LOGIN
For login use 
    - username: test_user
    - password: test_pwd

APP PAGES DESCRIPTION:
- Login page. User must be logged in to interact with the Calorie Tracker.
- Dashboard. Summary view for the user.
            - Displays targets, total calories and macronutrients user ate per day.
              Only 5 dates displayed on a page (sorted by dates in descending order),
              buttons 'Previous' and 'Next' used to navigate between pages.
            - Click on a date opens a daily nutrition view. 
            - Click on 'Edit meals' button opens page with options for viewing and editing
              meals, as well as creating new meals or snacks.
            - Dashboard view also includes 'Log Out' button for logging out.
            - User can always navigate back to the Dashboard from any page of the app by clicking
              'Back to Dashboard' button.
- Targets page. Lets use to edit targets. 
            - All fields are required. Inputs must be integers between 0 and 10,000.
- Adding new entry page. Lets user to add a new entry. 
            - When navigated from the Dashboard, automatically displays current date. 
            - All fields are required. Inputs for calories, protein, fats, and carbohydrates must
              be integers between 0 and 10,000.
            - Meal selection is also required (one per entry).
- Day view. Displays summary for the day: how much was eaten, how much left based on set targets, 
            and all entries for the day.
            - The entries are sorted by timestamps when they were created in descending order and
            by meal names if timestamps are the same.
                - Notes:
                       - The timestamps are not pretty but I kept them that way to fulfill the requirement
                         for clearly displayed sorting values.
                       - Date associated with the entry and date in 'Added at' timestamp for the entry maybe 
                         differ (and will differ for seed data).
            - The entries are diaplayed 5 at a time. Buttons 'Previous' and 'Next' used to navigate between pages.
            - A new entry can be added for the day by clicking on 'Add new entry button'.
- Day view without entries.
            - If no entries available for the day (eg after deleting the only entry associated with
              the date), a simple page displayed with buttons 'Add new entry' and 'Back to Dashboard'
- Meals view. Displays all meal options currently available for user in alphabetical order.
            - User can click on any meal option to edit and delete it
            - User can also add a new option for a meal or snack.
            - Warning is shown on the page that deleting meals will lead to deletion of any entries that
              include those meals. Editing meals will update existing entries. The actions cannot be undone.
                  - Design choices: This is done to fulfill requriement for deleting associated entries
                    (ON DELETE CASCADE) when referenced entries are deleted and to avoid many-to-many 
                    relationships between `nutrition` and `meals` relations.
- Adding meal. Meal names must be unique (for the user) and must be between 2 and 100 characters.
- Editing meal. Allows to edit or delete the meal entry. 
            - For editing: new meal name must be unique (for the user) and must be between 2 and 100 
              characters. Updating meal name will lead to updating all nutrition entries that reference
              that meal.
            - For deleting: deleting a meal will lead to deletign all nutrition entries that reference
              that meal.