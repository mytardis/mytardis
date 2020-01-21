import moment from "moment";


export const naturalDay = (date) => {
  //get moment data from passed date
  const momentDate = moment(date);
  if (!momentDate.isValid()){
    //passed date is not valid
    return date
  }
  //calculate difference in days from today
  const diffDays = moment().diff(moment(date),'days');
  const durationDays = moment.duration(diffDays, 'days').asDays();
  if(durationDays === 0){
    return "today"
  } else if(durationDays === 1 ){
    return "yesterday"
  } else if (durationDays > 1 && durationDays < 7){
    return 'a week ago'
  } else {
    return momentDate.format('Do MMMM YYYY');
  }
  
};