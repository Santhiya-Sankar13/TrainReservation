from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)


# PostgreSQL connection
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="train_reservation",
        user="postgres",
        password="TrainReserve@123",
        port="5432"
    )


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Train search
@app.route("/search", methods=["POST"])
def search_trains():

    source = request.form["source"]
    destination = request.form["destination"]
    journey_date = request.form["journey_date"]

    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT
            t.train_number,
            t.train_name,
            t.train_type,
            s1.station_name AS source,
            s2.station_name AS destination,
            r1.departure_time,
            r2.arrival_time
        FROM trains t

        JOIN train_routes r1
            ON t.train_id = r1.train_id

        JOIN stations s1
            ON r1.station_id = s1.station_id

        JOIN train_routes r2
            ON t.train_id = r2.train_id

        JOIN stations s2
            ON r2.station_id = s2.station_id

        WHERE s1.station_code = %s
        AND s2.station_code = %s
        AND r1.station_order < r2.station_order
    """

    cur.execute(query, (source, destination))

    trains = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
    "index.html",
    trains=trains,
    source=source,
    destination=destination,
    journey_date=journey_date
)
@app.route("/book", methods=["POST"])
def book_train():

    train_number = request.form["train_number"]
    source = request.form["source"]
    destination = request.form["destination"]
    journey_date = request.form["journey_date"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT train_name
        FROM trains
        WHERE train_number = %s
    """, (train_number,))

    result = cur.fetchone()

    cur.close()
    conn.close()

    train_name = result[0] if result else "Train"

    return render_template(
        "booking.html",
        train_number=train_number,
        train_name=train_name,
        source=source,
        destination=destination,
        journey_date=journey_date
    )
@app.route("/confirm-booking", methods=["POST"])
def confirm_booking():

    train_number = request.form["train_number"]
    source = request.form["source"]
    destination = request.form["destination"]
    journey_date = request.form["journey_date"]

    passenger_name = request.form["passenger_name"]
    age = request.form["age"]
    gender = request.form["gender"]

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT train_id, train_name
        FROM trains
        WHERE train_number = %s
    """, (train_number,))

    train = cur.fetchone()

    if not train:
        cur.close()
        conn.close()
        return "Train not found"

    train_id = train[0]
    train_name = train[1]

    # Get available seats for the selected journey segment
    cur.execute("""
        SELECT
            s.seat_id,
            c.coach_name,
            s.seat_number
        FROM seats s
        JOIN coaches c
            ON c.coach_id = s.coach_id
        WHERE c.train_id = %s
        AND NOT EXISTS (
            SELECT 1
            FROM seat_allocations sa
            JOIN bookings b
                ON b.booking_id = sa.booking_id
            WHERE sa.seat_id = s.seat_id
              AND b.status = 'CONFIRMED'
              AND sa.from_station_order <
                  (
                    SELECT r2.station_order
                    FROM train_routes r2
                    JOIN stations st2
                      ON st2.station_id = r2.station_id
                    WHERE r2.train_id = %s
                      AND st2.station_code = %s
                  )
              AND sa.to_station_order >
                  (
                    SELECT r1.station_order
                    FROM train_routes r1
                    JOIN stations st1
                      ON st1.station_id = r1.station_id
                    WHERE r1.train_id = %s
                      AND st1.station_code = %s
                  )
        )
        ORDER BY c.coach_name, s.seat_number
    """, (
        train_id,
        train_id, destination,
        train_id, source
    ))

    seats = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "seat_selection.html",
        seats=seats,
        train_number=train_number,
        train_name=train_name,
        source=source,
        destination=destination,
        journey_date=journey_date,
        passenger_name=passenger_name,
        age=age,
        gender=gender
    )
@app.route("/final-booking", methods=["POST"])
def final_booking():

    train_number = request.form["train_number"]
    source = request.form["source"]
    destination = request.form["destination"]
    journey_date = request.form["journey_date"]

    passenger_name = request.form["passenger_name"]
    age = request.form["age"]
    gender = request.form["gender"]
    seat_id = request.form["seat_id"]

    conn = get_db_connection()
    cur = conn.cursor()

    # Get train
    cur.execute("""
        SELECT train_id, train_name
        FROM trains
        WHERE train_number = %s
    """, (train_number,))

    train = cur.fetchone()

    if not train:
        cur.close()
        conn.close()
        return "Train not found"

    train_id = train[0]
    train_name = train[1]

    # Get station orders
    cur.execute("""
        SELECT station_order
        FROM train_routes r
        JOIN stations s
            ON s.station_id = r.station_id
        WHERE r.train_id = %s
        AND s.station_code = %s
    """, (train_id, source))

    from_order = cur.fetchone()[0]

    cur.execute("""
        SELECT station_order
        FROM train_routes r
        JOIN stations s
            ON s.station_id = r.station_id
        WHERE r.train_id = %s
        AND s.station_code = %s
    """, (train_id, destination))

    to_order = cur.fetchone()[0]

    # Check selected seat availability
    cur.execute("""
        SELECT 1
        FROM seat_allocations sa
        JOIN bookings b
            ON b.booking_id = sa.booking_id
        WHERE sa.seat_id = %s
        AND b.status = 'CONFIRMED'
        AND sa.from_station_order < %s
        AND sa.to_station_order > %s
    """, (seat_id, to_order, from_order))

    already_booked = cur.fetchone()

    if already_booked:
        cur.close()
        conn.close()
        return "Sorry! This seat is already booked for this journey segment."

    # Create PNR
    pnr = "PNR" + str(__import__("random").randint(10000, 99999))

    # Create booking
    cur.execute("""
        INSERT INTO bookings
        (pnr, user_id, train_id, source_station,
         destination_station, total_fare, status)
        SELECT
            %s,
            user_id,
            %s,
            s1.station_id,
            s2.station_id,
            450.00,
            'CONFIRMED'
        FROM users,
             stations s1,
             stations s2
        WHERE users.email = 'santhiya@gmail.com'
        AND s1.station_code = %s
        AND s2.station_code = %s
        RETURNING booking_id
    """, (pnr, train_id, source, destination))

    booking = cur.fetchone()

    if not booking:
        conn.rollback()
        cur.close()
        conn.close()
        return "User or station details not found."

    booking_id = booking[0]

    # Add passenger
    cur.execute("""
        INSERT INTO passengers
        (booking_id, passenger_name, age, gender, seat_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        booking_id,
        passenger_name,
        age,
        gender,
        seat_id
    ))

    # Add segment-based seat allocation
    cur.execute("""
        INSERT INTO seat_allocations
        (booking_id, seat_id, from_station_order, to_station_order)
        VALUES (%s, %s, %s, %s)
    """, (
        booking_id,
        seat_id,
        from_order,
        to_order
    ))

    # Add payment
    cur.execute("""
        INSERT INTO payments
        (booking_id, amount, payment_method, payment_status)
        VALUES (%s, 450.00, 'UPI', 'SUCCESS')
    """, (booking_id,))

    conn.commit()

    cur.close()
    conn.close()

    return f"""
    <html>
    <head>
        <title>Booking Confirmed</title>
    </head>

    <body style="font-family: Arial; text-align:center; padding:50px;">

        <h1>🎉 Booking Confirmed!</h1>

        <h2>🚆 {train_name}</h2>

        <p><strong>PNR:</strong> {pnr}</p>

        <p><strong>Passenger:</strong> {passenger_name}</p>

        <p><strong>Journey:</strong> {source} → {destination}</p>

        <p><strong>Journey Date:</strong> {journey_date}</p>

        <p><strong>Seat ID:</strong> {seat_id}</p>

        <p><strong>Fare:</strong> ₹450</p>

        <br>

        <a href="/">
            <button style="padding:12px 25px;">
                Back to Home
            </button>
        </a>

    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)