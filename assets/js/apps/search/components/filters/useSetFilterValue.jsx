import {  useDispatch, batch } from "react-redux";
import { updateFilter, removeFilter } from "../filterSlice";
import { runSearch } from "../searchSlice";

const useSetFilterValue = (fieldInfo) => {
    const { kind,target } = fieldInfo;
    const dispatch = useDispatch();
    const setFilterValue = (value) => {
        const dispatchValue = {
            field:fieldInfo,
            value
        };
        batch(() => {
            if (value === null) {
                dispatch(removeFilter(dispatchValue));
            } else {
                dispatch(updateFilter(dispatchValue));
            }
            dispatch(runSearch());
        });
    };
    return setFilterValue;
};

export default useSetFilterValue;