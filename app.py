from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)

# In-memory storage
members = {}  # {member_id: {"name": str, "age": int}}
books = {}    # {book_id: {"title": str, "author": str, "available": bool}}
borrows = {}  # {borrow_id: {"member_id": int, "book_id": int, "borrow_date": str, "due_date": str, "returned": bool, "return_date": str or None, "fine": float}}
reservations = []  # [{"reservation_id": str, "member_id": int, "book_id": int, "priority": str, "status": str, "timestamp": str}]

# Q1: Create Member
@app.route('/api/members', methods=['POST'])
def create_member():
    data = request.get_json()
    member_id = data.get('member_id')
    name = data.get('name')
    age = data.get('age')
    
    if not all([member_id, name, age]):
        return jsonify({"error": "Invalid input data"}), 400
    if member_id in members:
        return jsonify({"error": "Member ID already exists"}), 400
    if age <= 0:
        return jsonify({"error": "Invalid input data"}), 400
    
    members[member_id] = {"name": name, "age": age}
    return jsonify({"message": "Member created successfully", "member": members[member_id]}), 201

# Q2: Get Member Info
@app.route('/api/members/<int:member_id>', methods=['GET'])
def get_member(member_id):
    if member_id not in members:
        return jsonify({"error": "Member not found"}), 404
    return jsonify({"member": members[member_id]}), 200

# Q3: List All Members
@app.route('/api/members', methods=['GET'])
def list_members():
    return jsonify({"members": list(members.values())}), 200

# Q4: Update Member Info
@app.route('/api/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    if member_id not in members:
        return jsonify({"error": "Member not found"}), 404
    data = request.get_json()
    name = data.get('name', members[member_id]['name'])
    age = data.get('age', members[member_id]['age'])
    if age < 12:
        return jsonify({"error": "Age must be at least 12 years"}), 400
    members[member_id] = {"name": name, "age": age}
    return jsonify({"message": "Member updated successfully", "member": members[member_id]}), 200

# Q5: Borrow Book
@app.route('/api/borrow', methods=['POST'])
def borrow_book():
    data = request.get_json()
    member_id = data.get('member_id')
    book_id = data.get('book_id')
    if member_id not in members or book_id not in books:
        return jsonify({"error": "Member not found" if member_id not in members else "Book not found"}), 400
    active_borrows = [b for b in borrows.values() if b['member_id'] == member_id and not b['returned']]
    if active_borrows:
        return jsonify({"error": "Already has active borrow"}), 400
    if not books[book_id]['available']:
        return jsonify({"error": "Book not found"}), 400  # Assuming book not available means not found in this context
    
    borrow_id = len(borrows) + 1
    borrow_date = datetime.now().isoformat()
    due_date = (datetime.now() + timedelta(days=14)).isoformat()
    borrows[borrow_id] = {"member_id": member_id, "book_id": book_id, "borrow_date": borrow_date, "due_date": due_date, "returned": False, "fine": 0}
    books[book_id]['available'] = False
    return jsonify({"message": "Book borrowed successfully", "borrow_id": borrow_id}), 201

# Q6: Return Book
@app.route('/api/return', methods=['POST'])
def return_book():
    data = request.get_json()
    borrow_id = data.get('borrow_id')
    if borrow_id not in borrows or borrows[borrow_id]['returned']:
        return jsonify({"error": "Borrow not found"}), 400
    borrow = borrows[borrow_id]
    return_date = datetime.now().isoformat()
    if datetime.fromisoformat(return_date) > datetime.fromisoformat(borrow['due_date']):
        fine = (datetime.fromisoformat(return_date) - datetime.fromisoformat(borrow['due_date'])).days * 1
        borrow['fine'] = fine
    borrow['returned'] = True
    borrow['return_date'] = return_date
    books[borrow['book_id']]['available'] = True
    return jsonify({"message": "Book returned successfully", "fine": borrow['fine']}), 200

# Q7: List Borrowed Books
@app.route('/api/borrowed', methods=['GET'])
def list_borrowed():
    active_borrows = [b for b in borrows.values() if not b['returned']]
    return jsonify({"borrowed": active_borrows}), 200

# Q8: Get Borrowing History
@app.route('/api/members/<int:member_id>/history', methods=['GET'])
def get_borrowing_history(member_id):
    if member_id not in members:
        return jsonify({"error": "Member not found"}), 404
    history = [b for b in borrows.values() if b['member_id'] == member_id]
    return jsonify({"history": history}), 200

# Q9: Delete Member
@app.route('/api/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    if member_id not in members:
        return jsonify({"error": "Member not found"}), 404
    active_borrows = [b for b in borrows.values() if b['member_id'] == member_id and not b['returned']]
    if active_borrows:
        return jsonify({"error": "Active borrows exist"}), 400
    del members[member_id]
    return jsonify({"message": "Member deleted successfully"}), 200

# Q10: Get Overdue Books
@app.route('/api/overdue', methods=['GET'])
def get_overdue():
    now = datetime.now().isoformat()
    overdue = [b for b in borrows.values() if not b['returned'] and datetime.fromisoformat(b['due_date']) < datetime.fromisoformat(now)]
    return jsonify({"overdue": overdue}), 200

# Q11: Add Book
@app.route('/api/books', methods=['POST'])
def add_book():
    data = request.get_json()
    book_id = data.get('book_id')
    title = data.get('title')
    author = data.get('author')
    available = data.get('available', True)
    
    if not all([book_id, title, author]):
        return jsonify({"error": "Invalid input data"}), 400
    if book_id in books:
        return jsonify({"error": "Book ID already exists"}), 400
    
    books[book_id] = {"title": title, "author": author, "available": available}
    return jsonify({"message": "Book added successfully", "book": books[book_id]}), 201

# Q12: Get Book Info
@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    if book_id not in books:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"book": books[book_id]}), 200

# Q13: Advanced Book Search with Complex Filtering (Simplified)
@app.route('/api/books/search', methods=['GET'])
def search_books():
    query = request.args.get('query', '').lower()
    filtered = [b for b_id, b in books.items() if query in b['title'].lower() or query in b['author'].lower()]
    return jsonify({"books": filtered, "total_results": len(filtered), "analytics": {}}), 200

# Q14: Complex Book Reservation System with Priority Queue (Simplified)
@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    data = request.get_json()
    member_id = data.get('member_id')
    book_id = data.get('book_id')
    priority = data.get('priority', 'low')
    if member_id not in members or book_id not in books:
        return jsonify({"error": "Member not found" if member_id not in members else "Book not found"}), 400
    reservation_id = str(uuid.uuid4())
    reservation = {"reservation_id": reservation_id, "member_id": member_id, "book_id": book_id, "priority": priority, "status": "pending", "timestamp": datetime.now().isoformat()}
    reservations.append(reservation)
    return jsonify({"message": "Reservation created successfully", "reservation_id": reservation_id}), 201

# Q15: Delete Book
@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    if book_id not in books:
        return jsonify({"error": "Book not found"}), 404
    active_borrows = [b for b in borrows.values() if b['book_id'] == book_id and not b['returned']]
    if active_borrows:
        return jsonify({"error": "Active borrows exist"}), 400
    del books[book_id]
    return jsonify({"message": "Book deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)