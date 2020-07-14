import { Default, Empty } from "./DateRangeFilter.stories";
import { render, fireEvent, waitFor, screen } from '@testing-library/react';

test('Start and end dates are rendered as specified', async () => {
    render(Default());
    const startDateEl = screen.getByLabelText("Start date"),
        endDateEl = screen.getByLabelText("End date");
    expect(startDateEl.value).toBe("01/05/2020");
    expect(endDateEl.value).toBe("05/28/2020");
});

test('Start date changes when end date becomes a date before it', async () => {
    render(Default());
    const startDateEl = screen.getByLabelText("Start date"),
        endDateEl = screen.getByLabelText("End date");
    const anotherDate = "12/30/2019";
    fireEvent.change(endDateEl, { target: {value: anotherDate } });
    // After changing the end date to an earlier date, 
    // we should see both the start and end date fields to be the same.
    await waitFor(() => expect(endDateEl.value).toBe(anotherDate));
    await waitFor(() => expect(startDateEl.value).toBe(anotherDate));
})