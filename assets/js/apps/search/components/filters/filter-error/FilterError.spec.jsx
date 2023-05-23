import React from 'react';
import { Default, CustomMessages, WithLabel } from "./FilterError.stories";
import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import addons, { mockChannel } from '@storybook/addons';
import { scryRenderedComponentsWithType } from "react-dom/test-utils";

describe("Filter Error component", () => {
    it('Should contain the default short error message.', () => {
        render(Default());
        const errorText = screen.getByLabelText('Filter error message');
        expect(errorText.innerHTML).toBe("Invalid input");
    })

    it('Should contain the default tooltip message', async () => {
        render(<Default {...Default.args} />);
        fireEvent.mouseOver(screen.getByLabelText('Filter error message'));
        await waitFor(() => {
            const tooltip = screen.getByLabelText('tooltip container');
            return expect(tooltip.innerHTML).toContain('longer message');
        })
    })

    it('Should contain a custom short error message', () => {
        render(<CustomMessages {...CustomMessages.args} />);
        const shortErrorMessage = screen.getByLabelText('Filter error message');
        expect(shortErrorMessage.innerHTML).toBe('custom short message');
    })

    it('Should contain a custom long error message', async () => {
        render(<CustomMessages {...CustomMessages.args} />);
        fireEvent.mouseOver(screen.getByLabelText('Filter error message'));
        await waitFor(() => {
            const tooltip = screen.getByLabelText('tooltip container');
            return expect(tooltip.innerHTML).toContain('custom long message');
        })
    })

})
