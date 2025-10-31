import { FunctionComponent } from 'react';
export interface StarsProps {
    /**
     * Describes the number of stars to be filled in (in .5 increments)
     */
    number: number;
    /**
     * Describes the total number of stars to be displayed.
     */
    total?: number;
    /**
     * Describes if the stars should be hidden from a screen reader.
     */
    ariaHidden?: boolean;
}
declare const Stars: FunctionComponent<StarsProps>;
export default Stars;
