import React, { useState } from 'react'
import CategoryFilter  from './CategoryFilter';
import { action } from '@storybook/addon-actions';

export default {
  component: CategoryFilter,
  title: 'Filters/Category filter',
  decorators: [story => <div style={{ padding: '3rem', width:"300px"  }}>{story()}</div>],
  excludeStories: /.*Data$/,
};

export const categoryData = {
    value: [{op:"is",content:"1"}],
    onValueChange: action('category checked changed'),
    options: {
        categories: {
            allIds: ["1", "2", "3"],
            byId: {
                "1": {
                    label:"DNseq"
                },
                "2": {
                    label:"RNseq"
                },
                "3": {
                    label:"Methylation"
                }
            }
        }
    }
};

export const noneSelectedCategoryData = Object.assign({}, categoryData, {
    value: null
})

export const checkAllByDefaultCategoryData = Object.assign({},categoryData, {
    value: null,
    options: {
        categories:categoryData.options.categories,
        checkAllByDefault: true
    }
});

// const useStatefulProps = (props) => {
//     const [categories, changeCategories] = useState(props.value);
//     return Object.assign({},props,{
//         value: categories,
//         onValueChange: changeCategories
//     });
// }

export const Default = () => (
    // const [categoryValue, changeValue] = 
    <CategoryFilter {...categoryData} />);

export const NoneSelected = () => (<CategoryFilter {...noneSelectedCategoryData} />);

export const CheckAllByDefault = () => (<CategoryFilter {...checkAllByDefaultCategoryData} />);