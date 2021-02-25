import moment from 'moment';
import { naturalDay } from '../utils/humanize';

describe('test humanize script', () => {
  it('should return today', () => {
    const today = naturalDay(moment());
    expect(today).toEqual('today');
  });
  it('should return yesterday', () => {
    const today = naturalDay(moment().subtract(1, 'days'));
    expect(today).toEqual('yesterday');
  });
  it('should return a week ago', () => {
    const today = naturalDay(moment().subtract(5, 'days'));
    expect(today).toEqual('a week ago');
  });
  it('should handle invalid date', () => {
    const date = naturalDay('not a valid date');
    expect(date).toEqual('not a valid date');
  });
});
