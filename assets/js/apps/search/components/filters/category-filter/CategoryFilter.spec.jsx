import { Default, NoneSelected, CheckAllByDefault } from "./CategoryFilter.stories";
import { render, fireEvent, waitFor, screen } from '@testing-library/react';
import addons, { mockChannel } from '@storybook/addons';

const getFields = (screen) => (
    [screen.getByLabelText("DNseq"),screen.getByLabelText("RNseq"),screen.getByLabelText("Methylation")]
)

it('should allow us to uncheck all filters if not checkAllByDefault', () => {
    render(Default());
    const [ firstOption ] = getFields(screen);
    fireEvent.click(firstOption);
    expect(firstOption.checked).toBeFalsy();
});

it('should not allow us to uncheck all filters if checkAllByDefault', () => {
    render(CheckAllByDefault());
    const fields = getFields(screen);
    fields.forEach(fireEvent.click);
    expect(fields[2].checked).toBeTruthy();
});

it('should deselect a value when checked, if checkAllByDefault and all options checked', () => {
    render(CheckAllByDefault());
    const [ firstOption, secondOption, thirdOption ] = getFields(screen);
    fireEvent.click(firstOption);
    expect(firstOption.checked).toBeFalsy();
    expect(secondOption.checked).toBeTruthy();
    expect(thirdOption.checked).toBeTruthy();
})