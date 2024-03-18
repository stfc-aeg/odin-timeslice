
import { React, useState } from 'react';
import CloseButton from 'react-bootstrap/CloseButton';
import ListGroup from 'react-bootstrap/ListGroup';

import { WithEndpoint } from 'odin-react';


const EmailListObject = (props) => {

    const {endpoint, email} = props;

    const EndpointCloseButton = WithEndpoint(CloseButton);


    return (
        <ListGroup.Item action style={{ display: "flex"}}>
            {email}
            <EndpointCloseButton endpoint={endpoint} event_type='click' fullpath="remove_email_address" value={email}
                                 style={{ marginLeft: "auto"}}/>
        </ListGroup.Item>
    )

}


export default EmailListObject;