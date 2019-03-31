import React, {Component} from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

class SearchDatePicker extends Component {
    constructor() {
        super();
        this.state = {
            startDate: new Date(),
            endDate: new Date(),
        };
        this.handleChangeStart = this.handleChangeStart.bind(this);
        this.handleChangeEnd = this.handleChangeEnd.bind(this);
    }

    handleChangeStart(date) {
        this.setState({
            startDate: date,
        });
    }

    handleChangeEnd(date) {
        this.setState({
            endDate: date,
        });
    }


    render() {
        return (
            <div>
                <DatePicker
                    selected={this.state.startDate}
                    onChange={this.handleChangeStart}
                    dateFormat={"dd/MM/yyyy"}
                />
                <DatePicker
                    selected={this.state.endDate}
                    onChange={this.handleChangeEnd}
                    dateFormat={"dd/MM/yyyy"}
                />
            </div>
        );
    }
}

export default SearchDatePicker;