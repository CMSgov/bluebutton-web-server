import _pt from "prop-types";
import React from 'react';
import FilledStar from './RoundedStarFilledIcon';
import HalfStar from './RoundedStarHalfIcon';
import EmptyStar from './RoundedStarEmptyIcon';

var RoundedStar = function RoundedStar(props) {
  if (props.variation === 'filled') {
    return /*#__PURE__*/React.createElement(FilledStar, props);
  } else if (props.variation === 'half') {
    return /*#__PURE__*/React.createElement(HalfStar, props);
  } else {
    return /*#__PURE__*/React.createElement(EmptyStar, props);
  }
};

RoundedStar.propTypes = {
  className: _pt.string,
  variation: _pt.oneOf(['filled', 'half', 'empty'])
};
export default RoundedStar;