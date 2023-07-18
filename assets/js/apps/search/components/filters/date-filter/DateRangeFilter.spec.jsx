/*eslint-env jest*/

import { Default, Empty } from "./DateRangeFilter.stories";
import { render, fireEvent, waitFor, screen } from "@testing-library/react";
import React from "react";

const getDateFields = (screenInstance) => (
    [
        screen.getByLabelText("Start"),
        screen.getByLabelText("End"),
        screen.getByText("Filter")
    ]
);

it("should render start and end dates as specified", async () => {
    render(<Default {...Default.args} onValueChange={() => {}} />);
    const [startDateEl, endDateEl] = getDateFields(screen);
    expect(startDateEl.value).toBe("2020-01-05");
    expect(endDateEl.value).toBe("2020-05-28");
});

it("should change start date when end date becomes a date before it", async () => {
    render(<Default {...Default.args} onValueChange={() => {}} />);
    let [startDateEl, endDateEl] = getDateFields(screen);
    const anotherDate = "2019-12-30";
    fireEvent.change(endDateEl, { target: {value: anotherDate } });
    // After changing the end date to an earlier date, 
    // we should see both the start and end date fields to be the same
    // Retrieve input elements again as we have replaced them
    // to get around the react-datetime bug.
    // https://github.com/arqex/react-datetime/issues/760

    [startDateEl, endDateEl] = getDateFields(screen);
    await waitFor(() => expect(endDateEl.value).toBe(anotherDate));
    await waitFor(() => expect(startDateEl.value).toBe(anotherDate));
});

it("should callback with right value after submitting", async () => {
    const mockHandleChangeFn = jest.fn();
    // Add mock handleChange function to monitor whether changes
    // are added.
    const props = Object.assign({}, Empty.args, {
        onValueChange: mockHandleChangeFn
    });
    render(<Empty {...props} />);
    const [startDateEl, endDateEl, filterButton] = getDateFields(screen);
    fireEvent.change(startDateEl, {target: {value: "2020-01-05"}});
    fireEvent.change(endDateEl, {target: {value: "2020-01-07"}});
    fireEvent.click(filterButton);
    await waitFor(
        () => {
            expect(mockHandleChangeFn).toHaveBeenCalledTimes(1);
            expect(mockHandleChangeFn).toBeCalledWith(
                [
                    {op: ">=", content: "2020-01-05"},
                    {op: "<=", content: "2020-01-07"}
                ]
            );
        }
    );
});

it("should callback with null after clearing a filter", async () => {
    const mockHandleChangeFn = jest.fn();
    const props = Object.assign({}, Default.args, {
        onValueChange: mockHandleChangeFn
    });
    render(<Default {...props} />);
    const [startDateEl, endDateEl, filterButton] = getDateFields(screen);
    // Clear the dates
    fireEvent.change(startDateEl, { target: { value: "" } });
    fireEvent.change(endDateEl, { target: { value: "" } });
    // Filter button should still be clickable to clear the field.
    expect(filterButton.disabled).toBeFalsy();
    fireEvent.click(filterButton);
    await waitFor(
        () => {
            expect(mockHandleChangeFn).toHaveBeenCalledTimes(1);
            expect(mockHandleChangeFn).toBeCalledWith(null);
        });
});


it('Should show an error message when ', async () => {
    const mockHandleChangeFn = jest.fn();
    const props = Object.assign({}, Default.args, {
        onValueChange: mockHandleChangeFn
    });
    render(<Default {...props} />);
    const [startDateEl, endDateEl, filterButton] = getDateFields(screen);
    // Input invalid dates
    fireEvent.change(startDateEl, { target: { value: "abcd" } });
    fireEvent.change(endDateEl, { target: { value: "efg" } });
    // Filter button should still be clickable to clear the field.
    expect(filterButton.disabled).toBeFalsy();
    expect(screen.getByLabelText('Filter error message').innerHTML).toContain('Invalid date');
})


// TODO Add test to check null is returned to clear a field
