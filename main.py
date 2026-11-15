from drafter import *
from dataclasses import dataclass
from bakery import assert_equal


@dataclass
class MaintenanceRecord:
    service_name: str
    service_mileage: int
    interval: int
    cost: float


@dataclass
class State:
    name: str
    current_mileage: int
    maintenance_budget: float
    records: list[MaintenanceRecord]


def valid_number(text: str) -> bool:
    """Check for a nonnegative number with at most one decimal point."""
    text = text.strip()
    if text == "":
        return False
    return text.replace(".", "", 1).isascii() and \
        text.replace(".", "", 1).isdigit()


def valid_mileage(text: str) -> bool:
    """Check whether text contains a nonnegative whole number."""
    return text.isascii() and text.isdigit()


def total_cost(records: list[MaintenanceRecord]) -> float:
    """Add the costs of all maintenance records."""
    total = 0.0
    for record in records:
        total += record.cost
    return total


def service_status(current: int, next_due: int) -> str:
    """Describe when a service is due based on mileage."""
    if current >= next_due:
        return "Due now or overdue"
    if next_due - current <= 500:
        return "Due soon"
    return "Not due yet"


def latest_records(
    records: list[MaintenanceRecord]
) -> list[MaintenanceRecord]:
    """Find the latest mileage record for each service name."""
    latest = []
    for record in records:
        found = False
        for position in range(len(latest)):
            if latest[position].service_name == record.service_name:
                found = True
                if record.service_mileage >= latest[position].service_mileage:
                    latest[position] = record
        if not found:
            latest.append(record)
    return latest


def error_page(state: State, message: str) -> Page:
    """Show an input error without changing the saved information."""
    return Page(state, [
        Header("Please check your information"),
        message,
        Button("Home", index),
        Button("Add Service", add_service),
        Button("Budget", budget)
    ])


@route
def index(state: State) -> Page:
    """Show the home page and profile inputs."""
    return Page(state, [
        Header("Car Maintenance Tracker"),
        "Welcome, " + state.name + "!",
        "Track completed services, upcoming maintenance, and costs.",
        "Saved mileage: " + str(state.current_mileage),
        "Your name:",
        TextBox("name", state.name),
        "Current mileage:",
        TextBox("current_mileage", str(state.current_mileage)),
        Button("Save Profile", save_profile),
        Button("Add Service", add_service),
        Button("Service History", history),
        Button("Upcoming Maintenance", upcoming),
        Button("Budget", budget)
    ])


@route
def save_profile(
    state: State, name: str, current_mileage: str
) -> Page:
    """Validate and update the user's name and mileage."""
    name = name.strip()
    current_mileage = current_mileage.strip()

    if name == "" or not valid_mileage(current_mileage):
        return error_page(state, "Enter a name and a valid whole-number mileage.")

    mileage = int(current_mileage)
    for record in state.records:
        if mileage < record.service_mileage:
            return error_page(
                state, "Current mileage cannot be below a saved service mileage."
            )

    state.name = name
    state.current_mileage = mileage
    return index(state)


@route
def add_service(state: State) -> Page:
    """Show the form for adding a maintenance record."""
    return Page(state, [
        Header("Add Service"),
        "Service name, such as oil change or tire rotation:",
        TextBox("service_name", ""),
        "Mileage when the service was completed:",
        TextBox("service_mileage", str(state.current_mileage)),
        "Miles between services, using your car's maintenance schedule:",
        TextBox("interval", ""),
        "Service cost in dollars:",
        TextBox("cost", ""),
        Button("Save Service", save_service),
        Button("Home", index)
    ])


@route
def save_service(
    state: State, service_name: str, service_mileage: str,
    interval: str, cost: str
) -> Page:
    """Validate the service information and add a new record."""
    service_name = service_name.strip().lower()
    service_mileage = service_mileage.strip()
    interval = interval.strip()
    cost = cost.strip()

    if service_name == "":
        return error_page(state, "Enter a service name.")

    if not valid_mileage(service_mileage) or not valid_mileage(interval):
        return error_page(state, "Mileage and interval must be whole numbers.")

    if int(interval) == 0:
        return error_page(state, "The service interval must be greater than zero.")

    if not valid_number(cost):
        return error_page(state, "Enter a nonnegative cost, such as 75.50.")

    if int(service_mileage) > state.current_mileage:
        return error_page(state, "Update your current mileage on the home page first.")

    state.records.append(MaintenanceRecord(
        service_name,
        int(service_mileage),
        int(interval),
        float(cost)
    ))
    return history(state)


@route
def history(state: State) -> Page:
    """Display every saved maintenance record."""
    content = [Header("Service History")]

    if len(state.records) == 0:
        content.append("No services have been added yet.")

    for record in state.records:
        content.append(
            record.service_name
            + " | Mileage: " + str(record.service_mileage)
            + " | Interval: " + str(record.interval) + " miles"
            + " | Cost: $" + str(round(record.cost, 2))
        )

    content.append("Total spent: $" + str(round(total_cost(state.records), 2)))
    content.append(Button("Add Service", add_service))
    content.append(Button("Home", index))
    return Page(state, content)


@route
def upcoming(state: State) -> Page:
    """Show the next due mileage for each type of service."""
    content = [
        Header("Upcoming Maintenance"),
        "Current mileage: " + str(state.current_mileage),
        "Estimates use your entered mileage intervals."
    ]

    if len(state.records) == 0:
        content.append("Add a service record to see upcoming maintenance.")

    for record in latest_records(state.records):
        next_due = record.service_mileage + record.interval
        content.append(
            record.service_name
            + " | Next due: " + str(next_due) + " miles"
            + " | " + service_status(state.current_mileage, next_due)
        )

    content.append(Button("Home", index))
    return Page(state, content)


@route
def budget(state: State) -> Page:
    """Compare all recorded spending with the user's budget."""
    spent = total_cost(state.records)
    remaining = state.maintenance_budget - spent

    content = [
        Header("Maintenance Budget"),
        "This budget covers all maintenance records entered in this tracker.",
        "Budget: $" + str(round(state.maintenance_budget, 2)),
        "Total spent: $" + str(round(spent, 2))
    ]

    if remaining < 0:
        content.append("Over budget by: $" + str(round(-remaining, 2)))
    else:
        content.append("Budget remaining: $" + str(round(remaining, 2)))

    content.append("Enter a new budget:")
    content.append(TextBox("maintenance_budget", str(state.maintenance_budget)))
    content.append(Button("Save Budget", save_budget))
    content.append(Button("Home", index))
    return Page(state, content)


@route
def save_budget(state: State, maintenance_budget: str) -> Page:
    """Validate and save the user's maintenance budget."""
    maintenance_budget = maintenance_budget.strip()

    if not valid_number(maintenance_budget):
        return error_page(state, "Enter a nonnegative budget, such as 500.00.")

    state.maintenance_budget = float(maintenance_budget)
    return budget(state)


def run_tests() -> None:
    """Test calculations, all routes, and rejected inputs."""
    assert_equal(valid_number("75.50"), True)
    assert_equal(valid_number("-5"), False)
    assert_equal(valid_number("abc"), False)
    assert_equal(valid_number("1.2.3"), False)
    assert_equal(valid_mileage("10000"), True)
    assert_equal(valid_mileage("10.5"), False)
    assert_equal(total_cost([]), 0.0)
    assert_equal(service_status(10000, 10000), "Due now or overdue")
    assert_equal(service_status(9500, 10000), "Due soon")
    assert_equal(service_status(9499, 10000), "Not due yet")

    state = State("Driver", 10000, 200.0, [])

    assert_equal(index(state).state, state)
    assert_equal(add_service(state).state, state)
    assert_equal(history(state).state, state)
    assert_equal(upcoming(state).state, state)
    assert_equal(budget(state).state, state)

    assert_equal(
        save_profile(state, "Ryan", "12000").state,
        State("Ryan", 12000, 200.0, [])
    )
    save_profile(state, "", "-1")
    assert_equal(state, State("Ryan", 12000, 200.0, []))

    assert_equal(
        save_service(state, "Oil Change", "10000", "5000", "75.50").state,
        State("Ryan", 12000, 200.0, [
            MaintenanceRecord("oil change", 10000, 5000, 75.50)
        ])
    )
    save_service(state, "Oil Change", "10000", "0", "75")
    assert_equal(len(state.records), 1)
    save_service(state, "Oil Change", "13000", "5000", "75")
    assert_equal(len(state.records), 1)
    assert_equal(total_cost(state.records), 75.50)

    assert_equal(
        save_budget(state, "300").state.maintenance_budget, 300.0
    )
    save_budget(state, "-20")
    assert_equal(state.maintenance_budget, 300.0)

    assert_equal(
        latest_records([
            MaintenanceRecord("oil change", 10000, 5000, 75.0),
            MaintenanceRecord("oil change", 5000, 5000, 60.0),
            MaintenanceRecord("tires", 9000, 6000, 40.0)
        ]),
        [
            MaintenanceRecord("oil change", 10000, 5000, 75.0),
            MaintenanceRecord("tires", 9000, 6000, 40.0)
        ]
    )


set_website_title("Car Maintenance Tracker")
set_site_information(
    author="Ryan Schrenk",
    description="Track car maintenance, upcoming services, and spending.",
    sources="Class examples, Drafter documentation, and ChatGPT.",
    planning=["planning.docx", "design.docx"],
    links=[]
)

run_tests()
start_server(State("Driver", 0, 500.0, []))
