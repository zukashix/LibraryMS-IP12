import mysql.connector
import pandas
import matplotlib.pyplot as plt

# import csv using pandas and fetch database host,user,password,fine_rate,return_days
data = pandas.read_csv('lbms_settings.csv')
FINE_RATE = int(data['fine_rate'][0])
RETURN_DAYS = int(data['return_days'][0])

# Initialize database and required tables
database = mysql.connector.connect(
    host=data['host'][0],
    user=data['user'][0],
    password=data['password'][0]
)

cursor = database.cursor()

cursor.execute('CREATE DATABASE IF NOT EXISTS LibraryMS;') # Make database and use it
cursor.execute('USE LibraryMS;')

cursor.execute('CREATE TABLE IF NOT EXISTS users (username VARCHAR(50) PRIMARY KEY, password VARCHAR(50), role VARCHAR(50));')
cursor.execute('CREATE TABLE IF NOT EXISTS books (book_id INT PRIMARY KEY, title VARCHAR(50), author VARCHAR(50), quantity INT, location VARCHAR(100));')
cursor.execute('CREATE TABLE IF NOT EXISTS borrowed_books (book_id INT, username VARCHAR(50), date_borrowed DATE, FOREIGN KEY (book_id) REFERENCES books(book_id), FOREIGN KEY (username) REFERENCES users(username));')

cursor.execute('INSERT IGNORE INTO users (username, password, role) VALUES ("admin", "admin", "admin");') # create default admin user



# Login user to the system

CURRENT_USER = {'username': None, 'role': None}

while True:
    print('''\n\n
        | ========================== Welcome to Library Management System ========================== |
        
        | 1. Login
        | 2. Register
        | 3. Exit
        
    ''')

    choice = input('    | Enter your choice => ')

    # Login user 
    if choice == '1':
        username = input('    | Enter your username => ')
        password = input('    | Enter your password => ')

        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s;', (username, password))
        user = cursor.fetchone()

        if user:
            CURRENT_USER['username'] = user[0]
            CURRENT_USER['role'] = user[2]

            print('    | Login successful!')
            input('    | Press enter to continue...')
            break
        else:
            print('    | Invalid username or password!')
            input('    | Press enter to continue...')
            continue

    # Register user to the system
    elif choice == '2':
        username = input('    | Enter your username => ')

        cursor.execute('SELECT * FROM users WHERE username = %s;', (username,))
        user = cursor.fetchone()

        if user:
            print('    | Username already exists. Cannot register!')
            input('    | Press enter to continue...')
            continue

        password = input('    | Enter your password => ')
        rolechoice = input('    | Do you want to register as an admin? (type yes if needed) => ')
        role = 'user'

        if rolechoice.lower() == 'yes': # Register as admin
            admin_username = input('    | Enter an admin\'s username => ')
            admin_password = input('    | Enter an admin\'s password => ')

            cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s AND role = "admin";', (admin_username, admin_password))
            admin = cursor.fetchone()

            if not admin:
                print('    | You are not an admin!')
                input('    | Press enter to continue...')
                continue

            role = 'admin'

        cursor.execute('INSERT INTO users (username, password, role) VALUES (%s, %s, %s);', (username, password, role))
        database.commit()

        print('    | User registered successfully!')
        input('    | Press enter to continue...')
        continue


    elif choice == '3':
        print('    | Goodbye!')
        break



# Admin and User functionalities
while CURRENT_USER['role'] == 'user':
    print(f'''\n\n
        | ========================== You are logged in as {CURRENT_USER['username']} ========================== |
        
        | 1. Find a book
        | 2. Borrow a book
        | 3. Return a book
        | 4. View borrowed books
        | 5. Exit
          
    ''')

    choice = input('    | Enter your choice => ')



    # Find a book
    if choice == '1':
        title = input('    | Enter the ID/Title/Author of the book => ')

        cursor.execute('SELECT * FROM books WHERE book_id = %s OR title = %s OR author = %s;', (title, title, title))
        books = cursor.fetchall()

        if not books:
            print('    | Book not found!')
        else:
            print('    | Books found:\n')
            for book in books:
                print(f'    | ID {book[0]} - {book[1]} by {book[2]} at {book[4]}')

        input('\n    | Press enter to continue...')
        continue



    # Borrow a book
    elif choice == '2':
        book_id = input('    | Enter the ID of the book => ')

        cursor.execute('SELECT * FROM books WHERE book_id = %s;', (book_id,))
        book = cursor.fetchone()

        if not book:
            print('    | Book not found!')
            input('    | Press enter to continue...')
            continue

        cursor.execute('SELECT * FROM borrowed_books WHERE book_id = %s AND username = %s;', (book_id, CURRENT_USER['username']))
        borrowed_book = cursor.fetchone()

        if borrowed_book:
            print('    | You have already borrowed this book!')
            input('    | Press enter to continue...')
            continue

        if book[3] == 0:
            print('    | Book not available!')
            input('    | Press enter to continue...')
            continue

        cursor.execute('INSERT INTO borrowed_books (book_id, username, date_borrowed) VALUES (%s, %s, CURDATE());', (book_id, CURRENT_USER['username']))
        cursor.execute('UPDATE books SET quantity = quantity - 1 WHERE book_id = %s;', (book_id,))
        database.commit()

        print(f'   | You have successfully borrowed {book[1]} by {book[2]}')
        print(f'   | Please return the book within {RETURN_DAYS} days to avoid a fine of Rs. {FINE_RATE} per day.')
        input('    | Press enter to continue...')
        continue



    # Return a book
    elif choice == '3':
        book_id = input('    | Enter the ID of the book => ')

        cursor.execute('SELECT * FROM borrowed_books WHERE book_id = %s AND username = %s;', (book_id, CURRENT_USER['username']))
        borrowed_book = cursor.fetchone()

        if not borrowed_book:
            print('    | You have not borrowed this book!')
            input('    | Press enter to continue...')
            continue

        cursor.execute('SELECT DATEDIFF(CURDATE(), date_borrowed) FROM borrowed_books WHERE book_id = %s AND username = %s;', (book_id, CURRENT_USER['username']))
        days = cursor.fetchone()[0]

        if days > RETURN_DAYS:
            fine = (days - RETURN_DAYS) * FINE_RATE
            print(f'    | You have returned the book {days - RETURN_DAYS} days late. Please pay a fine of Rs. {fine}.')

        cursor.execute('DELETE FROM borrowed_books WHERE book_id = %s AND username = %s;', (book_id, CURRENT_USER['username']))
        cursor.execute('UPDATE books SET quantity = quantity + 1 WHERE book_id = %s;', (book_id,))
        database.commit()

        print(f'    | Book returned successfully! Returned in {days} days.')
        input('    | Press enter to continue...')
        continue



    # View borrowed books
    elif choice == '4':
        cursor.execute('SELECT * FROM borrowed_books WHERE username = %s;', (CURRENT_USER['username'],))
        borrowed_books = cursor.fetchall()

        if not borrowed_books:
            print('    | You have not borrowed any books!')
        else:
            print('    | Books borrowed:\n')
            for borrowed_book in borrowed_books:
                cursor.execute('SELECT * FROM books WHERE book_id = %s;', (borrowed_book[0],))
                book = cursor.fetchone()
                print(f'    | ID {book[0]} - {book[1]} by {book[2]} at {book[4]} on {borrowed_book[2]}')

        input('\n    | Press enter to continue...')
        continue



    # Exit
    elif choice == '5':
        print('    | Goodbye!')
        break



    else:
        print('    | Invalid choice!')
        input('    | Press enter to continue...')
        continue



while CURRENT_USER['role'] == 'admin':
    print(f'''\n\n
        | ========================== You are logged in as {CURRENT_USER['username']} ========================== |
        
        | 1. Add a book
        | 2. Remove a book
        | 3. Issue a book to a user
        | 4. Accept book return from a user
        | 5. Search a book by ID / Title / Author
        | 6. Search borrowed books by user
        | 7. Search borrowed books by book ID / Title / Author
        | 8. List all books
        | 9. List borrowed books
        | 10. List all users
        | 11. Remove a user
        | 12. Visualize available books
        | 13. Visualize borrowed books by user
        | 14. Visualize borrowed books by book
        | 15. Exit
          
    ''')


    choice = input('    | Enter your choice => ')



    # Add a book
    if choice == '1':
        id = int(input('    | Enter the ID of the book => '))

        cursor.execute('SELECT * FROM books WHERE book_id = %s;', (id,))
        book = cursor.fetchone()

        if book:
            print('    | Book already exists!')
            input('    | Press enter to continue...')
            continue

        title = input('    | Enter the title of the book => ')
        author = input('    | Enter the author of the book => ')
        quantity = int(input('    | Enter the quantity of the book => '))
        location = input('    | Enter the location of the book => ')

        cursor.execute('INSERT INTO books (book_id, title, author, quantity, location) VALUES (%s, %s, %s, %s, %s);', (id, title, author, quantity, location))
        database.commit()

        print('    | Book added successfully!')
        input('    | Press enter to continue...')
        continue



    # Remove a book
    elif choice == '2':
        book_id = input('    | Enter the ID of the book => ')

        cursor.execute('SELECT * FROM books WHERE book_id = %s;', (book_id,))
        book = cursor.fetchone()

        if not book:
            print('    | Book not found!')
            input('    | Press enter to continue...')
            continue

        cursor.execute('DELETE FROM books WHERE book_id = %s;', (book_id,))
        database.commit()

        print('    | Book removed successfully!')
        input('    | Press enter to continue...')
        continue



    # Issue a book to a user
    elif choice == '3':
        book_id = input('    | Enter the ID of the book => ')
        username = input('    | Enter the username of the user => ')

        cursor.execute('SELECT * FROM users WHERE username = %s;', (username,))
        user = cursor.fetchone()

        if not user:
            print('    | User not found!')
            input('    | Press enter to continue...')
            continue

        cursor.execute('SELECT * FROM books WHERE book_id = %s;', (book_id,))
        book = cursor.fetchone()

        if not book:
            print('    | Book not found!')
            input('    | Press enter to continue...')
            continue

        if book[3] == 0:
            print('    | Book not available!')
            input('    | Press enter to continue...')
            continue

        cursor.execute('INSERT INTO borrowed_books (book_id, username, date_borrowed) VALUES (%s, %s, CURDATE());', (book_id, username))
        cursor.execute('UPDATE books SET quantity = quantity - 1 WHERE book_id = %s;', (book_id,))
        database.commit()

        print(f'    | Book {book[1]} by {book[2]} issued to {username} successfully!')
        input('    | Press enter to continue...')
        continue



    # Accept book return from a user
    elif choice == '4':
        username = input('    | Enter the username of the user => ')

        cursor.execute('SELECT * FROM borrowed_books WHERE username = %s;', (username,))
        borrowed_books = cursor.fetchall()

        if not borrowed_books:
            print('    | User has not borrowed any books!')
            input('    | Press enter to continue...')
            continue

        print('    | Books borrowed by the user:\n')
        for borrowed_book in borrowed_books:
            cursor.execute('SELECT * FROM books WHERE book_id = %s;', (borrowed_book[0],))
            book = cursor.fetchone()
            print(f'    | ID {book[0]} - {book[1]} by {book[2]} on {borrowed_book[2]}')

        book_id = input('\n    | Enter the ID of the book to be returned => ')

        cursor.execute('SELECT * FROM borrowed_books WHERE book_id = %s AND username = %s;', (book_id, username))
        borrowed_book = cursor.fetchone()

        if not borrowed_book:
            print('    | User has not borrowed this book!')
            input('    | Press enter to continue...')
            continue

        cursor.execute('SELECT DATEDIFF(CURDATE(), date_borrowed) FROM borrowed_books WHERE book_id = %s AND username = %s;', (book_id, username))
        days = cursor.fetchone()[0]

        if days > RETURN_DAYS:
            fine = (days - RETURN_DAYS) * FINE_RATE
            print(f'    | User has returned the book {days - RETURN_DAYS} days late. Please ask for a fine of Rs. {fine}.')

        cursor.execute('DELETE FROM borrowed_books WHERE book_id = %s AND username = %s;', (book_id, username))
        cursor.execute('UPDATE books SET quantity = quantity + 1 WHERE book_id = %s;', (book_id,))
        database.commit()

        print(f'    | Book returned successfully! Returned in {days} days.')
        input('    | Press enter to continue...')
        continue



    # Search a book by ID / Title / Author
    elif choice == '5':
        title = input('    | Enter the ID/Title/Author of the book => ')

        cursor.execute('SELECT * FROM books WHERE book_id = %s OR title = %s OR author = %s;', (title, title, title))
        books = cursor.fetchall()

        if not books:
            print('    | Book not found!')
        else:
            print('    | Books found:\n')
            for book in books:
                print(f'    | ID {book[0]} - {book[1]} by {book[2]} at {book[4]} with quantity {book[3]}')

        input('\n    | Press enter to continue...')
        continue



    # Search borrowed books by user
    elif choice == '6':
        username = input('    | Enter the username of the user => ')

        cursor.execute('SELECT * FROM borrowed_books WHERE username = %s;', (username,))
        borrowed_books = cursor.fetchall()

        if not borrowed_books:
            print('    | User has not borrowed any books!')
        else:
            print('    | Books borrowed by the user:\n')
            for borrowed_book in borrowed_books:
                cursor.execute('SELECT * FROM books WHERE book_id = %s;', (borrowed_book[0],))
                book = cursor.fetchone()
                print(f'    | ID {book[0]} - {book[1]} by {book[2]} on {borrowed_book[2]}')

        input('\n    | Press enter to continue...')
        continue



    # Search borrowed books by book ID / Title / Author
    elif choice == '7':
        title = input('    | Enter the ID/Title/Author of the book => ')

        cursor.execute('SELECT * FROM books WHERE book_id = %s OR title = %s OR author = %s;', (title, title, title))
        books = cursor.fetchall()

        if not books:
            print('    | Book not found!')
        else:
            print('    | Books found:\n')
            for book in books:
                cursor.execute('SELECT * FROM borrowed_books WHERE book_id = %s;', (book[0],))
                borrowed_books = cursor.fetchall()

                if not borrowed_books:
                    print(f'    | ID {book[0]} - {book[1]} by {book[2]} at {book[4]} is not borrowed by anyone!')
                else:
                    print(f'    | ID {book[0]} - {book[1]} by {book[2]} at {book[4]} is borrowed by:')
                    for borrowed_book in borrowed_books:
                        print(f'    | {borrowed_book[1]} on {borrowed_book[2]}')

        input('\n    | Press enter to continue...')
        continue


   
    # List all books
    elif choice == '8':
        cursor.execute('SELECT * FROM books;')
        books = cursor.fetchall()

        if not books:
            print('    | No books available!')
        else:
            print('    | Books available:\n')
            for book in books:
                print(f'    | ID {book[0]} - {book[1]} by {book[2]} at {book[4]}')

        input('\n    | Press enter to continue...')
        continue



    # List borrowed books
    elif choice == '9':
        cursor.execute('SELECT * FROM borrowed_books;')
        borrowed_books = cursor.fetchall()

        if not borrowed_books:
            print('    | No books borrowed!')
        else:
            print('    | Books borrowed:\n')
            for borrowed_book in borrowed_books:
                cursor.execute('SELECT * FROM books WHERE book_id = %s;', (borrowed_book[0],))
                book = cursor.fetchone()
                print(f'    | ID {book[0]} - {book[1]} by {book[2]} on {borrowed_book[2]}')

        input('\n    | Press enter to continue...')
        continue



    # List all users
    elif choice == '10':
        cursor.execute('SELECT * FROM users;')
        users = cursor.fetchall()

        if not users:
            print('    | No users available!')
        else:
            print('    | Users available:\n')
            for user in users:
                print(f'    | {user[0]} - {user[2]}')

        input('\n    | Press enter to continue...')
        continue



    # Remove a user
    elif choice == '11':
        username = input('    | Enter the username of the user => ')

        cursor.execute('DELETE FROM users WHERE username = %s;', (username,))
        database.commit()

        print('    | User removed successfully!')
        input('    | Press enter to continue...')
        continue



    # Visualize available books
    elif choice == '12':
        cursor.execute('SELECT title, quantity FROM books;')
        books = cursor.fetchall()

        if not books:
            print('    | No books available!')
            input('    | Press enter to continue...')
            continue

        titles = [book[0] for book in books]
        quantities = [book[1] for book in books]

        plt.bar(titles, quantities)
        plt.xlabel('Titles')
        plt.ylabel('Quantities')
        plt.title('Available Books')
        plt.show()

        input('    | Press enter to continue...')
        continue



    # Visualize borrowed books by user
    elif choice == '13':
        cursor.execute('SELECT username, COUNT(*) FROM borrowed_books GROUP BY username;')
        users = cursor.fetchall()

        if not users:
            print('    | No books borrowed!')
            input('    | Press enter to continue...')
            continue

        usernames = [user[0] for user in users]
        counts = [user[1] for user in users]

        plt.bar(usernames, counts)
        plt.xlabel('Usernames')
        plt.ylabel('No. Of Books')
        plt.title('Borrowed Books by User')
        plt.show()

        input('    | Press enter to continue...')
        continue



    # Visualize borrowed books by book title
    elif choice == '14':
        cursor.execute('SELECT books.title, COUNT(*) FROM borrowed_books JOIN books ON borrowed_books.book_id = books.book_id GROUP BY books.title;')
        books = cursor.fetchall()

        if not books:
            print('    | No books borrowed!')
            input('    | Press enter to continue...')
            continue

        titles = [book[0] for book in books]
        counts = [book[1] for book in books]

        plt.bar(titles, counts)
        plt.xlabel('Titles')
        plt.ylabel('No. Of Books')
        plt.title('Borrowed Books by Title')
        plt.show()

        input('    | Press enter to continue...')
        continue



    # Exit
    elif choice == '15':
        print('    | Goodbye!')
        break



    else:
        print('    | Invalid choice!')
        input('    | Press enter to continue...')
        continue


# close database connection
cursor.close()
database.close()
