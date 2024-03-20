import logo from './logo.svg';
import './App.css';

import React, {useState} from 'react';

import { OdinApp, TitleCard, WithEndpoint, useAdapterEndpoint } from 'odin-react';

import styles from './App.css'

import 'odin-react/dist/index.css'
import 'bootstrap/dist/css/bootstrap.min.css';

import Container from 'react-bootstrap/Container';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import Stack from 'react-bootstrap/Stack';
import ListGroup from 'react-bootstrap/ListGroup';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import Modal from 'react-bootstrap/Modal';
import Accordion from 'react-bootstrap/Accordion';
import NavBar from 'react-bootstrap/Navbar';


import VideoThumbnail from './VideoThumbnail';
import EmailListObject from './EmailListObject';

const EndpointButton = WithEndpoint(Button);

const video_columns = 2;
const code_columns = 5;

function App() {

  const endpoint = useAdapterEndpoint("timeslice", process.env.REACT_APP_ENDPOINT_URL);

  const [code, changeCode] = useState("");
  const [email, changeEmail] = useState("");
  const [modal_show, changeModalShow] = useState(false);
  const [email_success, changeEmailSuccess] = useState(false);
  const [logo_hover, changeLogoHover] = useState(false);

  const handleShow = () => changeModalShow(true);
  const handleHide = () => changeModalShow(false);

  const handleHoverOn = () => changeLogoHover(true);
  const handleHoverOff = () => changeLogoHover(false);
    
  const codeChangeHandler = (event) => {
    console.log(event);
    changeCode(event.target.value);
  }

  const emailChangeHandler = (event) => {
    console.log(event);
    changeEmail(event.target.value);
  }

  const videoClickHandler = (selected, code) => {
    console.log(`Add/Remove Code ${code}`);
    const sendVal = {[selected ? "add_access_code" : "remove_access_code"]: code};

    endpoint.put(sendVal)
    .then((response) => {
      console.log("Successfull put code");
      endpoint.mergeData(response, "");
      changeEmailSuccess(true);
    })
    .catch((err) => {
      console.log(err);
      changeEmailSuccess(false);
    });
  }

  const postEmailCleanup = () => {
    if(email_success)
    {
      console.log("Email Sent, clearing up inputs");
      endpoint.put({"clear_access_codes": true}).then((response) => endpoint.mergeData(response, ""));
      endpoint.put({"clear_email": true}).then((response) => endpoint.mergeData(response, ""));
      changeCode("");
      changeEmail("");
      handleShow();
    }
  }
  const video_list_reshaper = (video_list, cols) => {
    var matrix = [], i, k;

    for(i = 0, k= -1; i< video_list.length; i++)
    {
      if( i % cols === 0)
      {
        k++;
        matrix[k] = [];
      }

      matrix[k].push(video_list[i]);
    }

    if(video_list.length % cols !== 0)
    {

    }

    return matrix;
  }

  const video_list_filler = (width) => {
    let filler_list = [];
    for(let i = width; i < video_columns; i ++)
    {
      filler_list.push((<Col></Col>));
    }
    return filler_list;
  }

  const video_list = (
    endpoint.data?.avail_file_list ? video_list_reshaper(endpoint.data.avail_file_list, video_columns).map(
    (selection, index) =>
    (
      
      <Row>
        {selection.map((sub_select, index) => (
        <Col>
          <VideoThumbnail src={`renders/${sub_select}`} title={sub_select.slice(0, -4)} clickHandler={videoClickHandler}
          isSelected={endpoint.data?.access_codes ? endpoint.data.access_codes.includes(sub_select.slice(0, -4)) : false}/>
        </Col>
        ))}
        {selection.length % video_columns === 0 ? (<></>) : video_list_filler(selection.length)}
        
      </Row>
    )) : <></>)

  const sent_video_list = (
    endpoint.data?.sent_file_list ? video_list_reshaper(endpoint.data.sent_file_list, video_columns).map(
      (selection, index) =>
      (
        <Row>
        {selection.map((sub_select, index) => (
        <Col>
          <VideoThumbnail src={`renders/${sub_select}`} title={sub_select.slice(0, -4)} clickHandler={videoClickHandler}
          isSelected={endpoint.data?.access_codes ? endpoint.data.access_codes.includes(sub_select.slice(0, -4)) : false}/>
        </Col>
        ))}
        {selection.length % video_columns === 0 ? (<></>) : video_list_filler(selection.length)}
        
      </Row>
    )) : <></>)

  const code_list = endpoint.data?.access_codes ? video_list_reshaper(endpoint.data.access_codes, code_columns).map(
    (code, index) => (
      <ListGroup horizontal>
        {code.map((sub_code, index) => (
          <ListGroup.Item>{sub_code}</ListGroup.Item>
        ))}
      </ListGroup>
    )) : <></>;

  const email_list = endpoint.data?.email_address ? endpoint.data.email_address.map(
    (list_email, index) => (
      
      <EmailListObject endpoint={endpoint} email={list_email}/>
    )
  ) : <></>;

  return (
    <>
   <NavBar data-bs-theme='dark' style={{background: '#505050'}}>
      <NavBar.Brand href='#'>
        {/* I added the pride logo as a hoverover easter egg. So sue me */}
        <img src={logo_hover ? 'UKRI_PRIDE_STFC_logo.png' : 'UKRI_STFC_logo.png'}
        height="35"
        style={{marginLeft: "5px", marginRight: "10px"}}
        alt='STFC Logo'
        onMouseEnter={handleHoverOn}
        onMouseLeave={handleHoverOff}/>
        Timeslice Camera Email Service
      </NavBar.Brand>
   </NavBar>
    
        <Container>
          <Row>
          <Col>
            <TitleCard title="Select Video Codes">
              
              <Form.Label>Enter video codes or select from the list</Form.Label>
              <InputGroup>
                <Form.Control onChange={codeChangeHandler} value={code}/>
                <EndpointButton endpoint={endpoint} event_type='click' fullpath="add_access_code" value={code}>
                  Add Code
                </EndpointButton>
              </InputGroup>
              <ListGroup>
                <ListGroup.Item variant='primary'>Selected Codes:</ListGroup.Item>
                {code_list}
              </ListGroup>
              <EndpointButton endpoint={endpoint} event_type="click" fullpath="clear_access_codes" value={true}>
                Clear Codes
              </EndpointButton>
            </TitleCard>
            <TitleCard title="Email">
              <Form.Label>
                Enter Email(s) to receive selected videos:
              </Form.Label>
              <InputGroup>
                <Form.Control onChange={emailChangeHandler} value={email}/>
                <EndpointButton endpoint={endpoint} event_type="click" fullpath="add_email_address" value={email}>
                  Add Email
                </EndpointButton>
              </InputGroup>
              <ListGroup>
                <ListGroup.Item variant='primary'>Email(s):</ListGroup.Item>
                {email_list}
              </ListGroup>
              <ButtonGroup>
                <EndpointButton variant="warning" endpoint={endpoint} event_type='click' fullpath="clear_email" value={true}>
                  Clear Email
                </EndpointButton>
                <EndpointButton endpoint={endpoint} event_type='click' fullpath="send_email_new" value={true}
                                post_method={postEmailCleanup}>
                  Send Email
                </EndpointButton>
              </ButtonGroup>
            </TitleCard>
          </Col>

          {/* Video Listing Column */}
          <Col style={{height: "90vh", overflowY: "auto"}}>
            <Row>
            <Col>
              <TitleCard title="Available Videos" className={styles.scrollStyle}>
                <Stack gap={2}>
                <EndpointButton endpoint={endpoint} event_type='click' fullpath="avail_file_list" value={[]}>
                  Refresh List
                </EndpointButton>
                <Row>
                  {video_list}
                </Row>
                </Stack>
              </TitleCard>
            </Col>
            </Row>
            <Row>
            <Col>
              <Accordion>
                <Accordion.Item eventKey='0'>
                  <Accordion.Header>Sent Videos</Accordion.Header>
                  <Accordion.Body>
                <Row>
                  {sent_video_list}
                </Row>
                </Accordion.Body>
                </Accordion.Item>
              </Accordion>
            </Col>
            </Row>
          </Col>
          </Row>

          <Modal show={modal_show} onHide={handleHide}>
            <Modal.Header closeButton>
              <Modal.Title>Email Sent</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              {email_success ? "The selected videos have been emailed! You may now close this popup." :
                               "Sending Email Failed. Check server logs for details."}
              
            </Modal.Body>
          </Modal>
        </Container>
      </>
  );
}

export default App;
