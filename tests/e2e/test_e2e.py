# tests/e2e/test_e2e.py

import pytest  # Import the pytest framework for writing and running tests
import uuid

# The following decorators and functions define E2E tests for the FastAPI calculator application.

@pytest.mark.e2e
def test_hello_world(page, fastapi_server):
    """
    Test that the homepage displays "Hello World".

    This test verifies that when a user navigates to the homepage of the application,
    the main header (`<h1>`) correctly displays the text "Hello World". This ensures
    that the server is running and serving the correct template.
    """
    # Navigate the browser to the homepage URL of the FastAPI application.
    page.goto('http://localhost:8000')
    
    # Use an assertion to check that the text within the first <h1> tag is exactly "Hello World".
    # If the text does not match, the test will fail.
    assert page.inner_text('h1') == 'Hello World'

@pytest.mark.e2e
def test_calculator_add(page, fastapi_server):
    """
    Test the addition functionality of the calculator.

    This test simulates a user performing an addition operation using the calculator
    on the frontend. It fills in two numbers, clicks the "Add" button, and verifies
    that the result displayed is correct.
    """
    # Navigate the browser to the homepage URL of the FastAPI application.
    page.goto('http://localhost:8000')
    
    # Fill in the first number input field (with id 'a') with the value '10'.
    page.fill('#a', '10')
    page.fill('#b', '5')

    with page.expect_response('**/add') as add_response:
        page.click('button:has-text("Add")')
    response = add_response.value
    assert response.status == 200

    page.wait_for_function("document.querySelector('#result').innerText.length > 0")
    assert page.inner_text('#result').strip() == 'Result: 15'

@pytest.mark.e2e
def test_calculator_divide_by_zero(page, fastapi_server):
    """
    Test the divide by zero functionality of the calculator.

    This test simulates a user attempting to divide a number by zero using the calculator.
    It fills in the numbers, clicks the "Divide" button, and verifies that the appropriate
    error message is displayed. This ensures that the application correctly handles invalid
    operations and provides meaningful feedback to the user.
    """
    # Navigate the browser to the homepage URL of the FastAPI application.
    page.goto('http://localhost:8000')
    
    # Fill in the first number input field (with id 'a') with the value '10'.
    page.fill('#a', '10')
    page.fill('#b', '0')

    with page.expect_response('**/divide') as divide_response:
        page.click('button:has-text("Divide")')
    response = divide_response.value
    assert response.status == 400

    page.wait_for_function("document.querySelector('#result').innerText.length > 0")
    assert page.inner_text('#result').strip() == 'Error: Cannot divide by zero!'


@pytest.mark.e2e
def test_register_and_login_pages(page, fastapi_server):
    # Register page should render and accept a new user registration.
    page.goto('http://localhost:8000/register')
    assert page.inner_text('h1') == 'Register'

    page.fill('#username', 'ui-test-user')
    page.fill('#email', 'ui-test-user@example.com')
    page.fill('#password', 'TestPass123')
    page.fill('#confirm_password', 'TestPass123')

    with page.expect_response('**/users/register') as register_response:
        page.click('button:has-text("Register")')
    response = register_response.value
    assert response.status == 201

    page.wait_for_function("document.querySelector('#message').innerText.length > 0")
    assert page.locator('#message').inner_text().strip() == 'Registration successful.'

    # Login page should render and accept the same credentials.
    page.goto('http://localhost:8000/login')
    assert page.inner_text('h1') == 'Login'

    page.fill('#username', 'ui-test-user')
    page.fill('#password', 'TestPass123')

    with page.expect_response('**/users/login') as login_response:
        page.click('button:has-text("Login")')
    response = login_response.value
    assert response.status == 200

    page.wait_for_function("document.querySelector('#message').innerText.length > 0")
    assert page.locator('#message').inner_text().strip() == 'Login successful.'
