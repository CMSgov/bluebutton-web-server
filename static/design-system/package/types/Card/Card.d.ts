import React from 'react';
import { FunctionComponent } from 'react';
interface CardProps {
    /**
     * Content to be displayed inside the card
     */
    children?: React.ReactNode;
    /**
     * Additional css class names to be added to the Card element
     */
    className?: string;
}
declare const Card: FunctionComponent<CardProps>;
export default Card;
