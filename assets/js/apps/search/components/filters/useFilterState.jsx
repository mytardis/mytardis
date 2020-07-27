import { useSelector,  useDispatch, batch } from "react-redux";
import { updateFilter, removeFilter } from "../filterSlice";
import { runSearch } from "../searchSlice";

const useFilterState = (fieldInfo) => {
    const { kind,target } = fieldInfo;
    const dispatch = useDispatch();
    const filterValue = useSelector(
        (state) => {
            switch(kind) {
                case "typeAttribute":
                    const [typeId, attributeId] = target;
                    return state.filters.types
                        .byId[typeId]
                        .attributes[attributeId]
                        .value;
                case "schemaParameter":
                    const [schemaId, paramId] = target;
                    return state.filters.schemas
                        .byId[schemaId]
                        .parameters[paramId]
                        .value;
                default:
                    break;
            }
        }
    );
    const setFilterValue = (value) => {
        const dispatchValue = {
            field:fieldInfo,
            value
        };
        batch(() => {
            if (value === null) {
                dispatch(removeFilter(dispatchValue));
            } else {
                dispatch(updateFilter(dispatchValue))
            }
            dispatch(runSearch());
        });
    };

    return [filterValue, setFilterValue];

};

export default useFilterState;