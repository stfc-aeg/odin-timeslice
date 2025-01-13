import { React } from "react";
import Alert from 'react-bootstrap/Alert';

const VideoThumbnail = (props) => {

    const {src, title, clickHandler, isSelected} = props;

    const onClickHandler = () => {
        clickHandler(!isSelected, title);
    }

    const onMouseEnterHandler = (event) => {
        event.target.play()
        .then().catch( (err) => {
        console.log(err.message)});
    }
    const onMouseLeaveHandler = (event) => {
        try {
            event.target.pause();
            event.target.currentTime = 0;
        } catch(err) {
            console.log(err.message);
        }
    }
    return (
        <Alert variant={isSelected ? "success" : "light"} onClick={onClickHandler}>
                <div className="emded-responsive">
                <video class="video-thumbnail" src={src} width="100%" onMouseEnter={onMouseEnterHandler} onMouseLeave={onMouseLeaveHandler}
                muted="muted" loop/>
                <div class="text-on-image">
                    <p>{title}</p>
                </div>
                </div>
        </Alert>
    )
}

export default VideoThumbnail;