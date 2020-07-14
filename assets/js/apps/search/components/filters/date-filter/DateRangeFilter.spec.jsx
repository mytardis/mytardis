import { Default, Empty } from "./DateRangeFilter.stories";
import { render, fireEvent, waitFor, screen } from '@testing-library/react';

const getDateFields = (screen) => (
    [
        screen.getByLabelText("Start date"), 
        screen.getByLabelText("End date"),
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
    render(Empty(mockHandleChangeFn));
    const [startDateEl, endDateEl,filterButton] = getDateFields(screen);
    fireEvent.change(startDateEl, {target: {value: "01/05/2020"}});
    fireEvent.change(endDateEl, {target: {value: "01/07/2020"}});
    fireEvent.click(filterButton);
    await waitFor(
        () => expect(mockHandleChangeFn).toBeCalledWith(
            [
                {op:">=",content:new Date("01/05/2020")},
                {op:"<=",content: new Date("01/07/2020")}
            ]
        )
    );

});