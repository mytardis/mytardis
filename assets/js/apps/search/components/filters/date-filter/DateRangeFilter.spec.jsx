import { Default, Empty } from "./DateRangeFilter.stories";
import { render, fireEvent, waitFor, screen } from '@testing-library/react';

const getDateFields = (screen) => (
    [
        screen.getByLabelText("Start"), 
        screen.getByLabelText("End"),
        screen.getByText("Filter")
    ]
)

it('should render start and end dates as specified', async () => {
    render(Default());
    const [startDateEl, endDateEl] = getDateFields(screen);
    expect(startDateEl.value).toBe("01/05/2020");
    expect(endDateEl.value).toBe("05/28/2020");
});

it('should change start date when end date becomes a date before it', async () => {
    render(Default());
    const [startDateEl, endDateEl] = getDateFields(screen);
    const anotherDate = "12/30/2019";
    fireEvent.change(endDateEl, { target: {value: anotherDate } });
    // After changing the end date to an earlier date, 
    // we should see both the start and end date fields to be the same.
    await waitFor(() => expect(endDateEl.value).toBe(anotherDate));
    await waitFor(() => expect(startDateEl.value).toBe(anotherDate));
});

it('should callback with right value after submitting', async () => {
    const mockHandleChangeFn = jest.fn();
    render(Empty(null,mockHandleChangeFn));
    const [startDateEl, endDateEl,filterButton] = getDateFields(screen);
    fireEvent.change(startDateEl, {target: {value: "01/05/2020"}});
    fireEvent.change(endDateEl, {target: {value: "01/07/2020"}});
    fireEvent.click(filterButton);
    await waitFor(
        () => {
            expect(mockHandleChangeFn).toHaveBeenCalledTimes(1);
            expect(mockHandleChangeFn).toBeCalledWith(
                [
                    {op:">=",content:new Date("01/05/2020").toISOString()},
                    {op:"<=",content: new Date("01/07/2020").toISOString()}
                ]
            );
        }
    );
});

it('should callback with null after clearing a filter', async () => {
    const mockHandleChangeFn = jest.fn();
    render(Default(null,mockHandleChangeFn));
    const [startDateEl, endDateEl,filterButton] = getDateFields(screen);
    // Clear the dates
    fireEvent.change(startDateEl, {target: {value: ""}});
    fireEvent.change(endDateEl, {target: {value: ""}});
    // Filter button should still be clickable to clear the field.
    expect(filterButton.disabled).toBeFalsy();
    fireEvent.click(filterButton);
    await waitFor(
        () => {
            expect(mockHandleChangeFn).toHaveBeenCalledTimes(1);
            expect(mockHandleChangeFn).toBeCalledWith(null);
    });
});


// TODO Add test to check null is returned to clear a field