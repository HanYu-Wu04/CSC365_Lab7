# Inn/Hotel Reservation System

This project implements an inn/hotel reservation system as part of the CSC 365 course requirements. The system allows users to perform a variety of operations related to room reservations.

## Team Members

- Han Yu Wu
- Evan Cao

## Running Instructions

1. **Install all requirements**: Run `pip install -r requirements.txt` to install the necessary Python packages.
2. **Environment setup**: Create a `.env` file in the project root directory with your database password and other sensitive configurations. Example content for `.env`: DB_PASSWORD='YourPasswordHere'
3. **Database configuration**: Adjust the database user and other configurations in `db_config.py` as necessary.
4. **Launch the application**: Run the main script with Python 3 by executing `python main.py` in your terminal.
5. **Navigate the menu**: Use the numeric options (e.g., enter `1` for FR1, `2` for FR2, etc.) to explore different functionalities of the reservation system.

## Known Bugs and/or Deficiencies

- There was a significant challenge encountered during the development of FR2. The initial query could not accurately filter and display the 5 possible room options. This issue was resolved after revising the query logic.

## Additional Notes

- The development process involved close collaboration between the team members, predominantly using a single machine for implementation.